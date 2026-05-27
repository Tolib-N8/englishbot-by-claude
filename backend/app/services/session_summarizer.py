"""Ask Claude to summarize a conversation into vault notes.

Architecture: Claude is a pure text generator. It outputs note bodies in a
strict block-fence format; Python parses them and writes the files. This
keeps the bot from having direct filesystem access.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.models.message import Message
from app.services.anthropic_client import claude_complete
from app.services.vault import list_notes, slugify, write_note

NOTE_BLOCK_RE = re.compile(
    r"<<<NOTE\s+path=\"([^\"]+)\"\s*>>>\n(.*?)\n<<<END_NOTE>>>",
    re.DOTALL,
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class ParsedNote:
    path: str
    frontmatter_text: str
    body: str


def _parse_blocks(reply: str) -> list[ParsedNote]:
    notes: list[ParsedNote] = []
    for m in NOTE_BLOCK_RE.finditer(reply):
        path = m.group(1).strip()
        content = m.group(2).strip()
        fm_match = FRONTMATTER_RE.match(content)
        if fm_match:
            frontmatter_text = fm_match.group(1).strip()
            body = fm_match.group(2).strip()
        else:
            frontmatter_text = ""
            body = content
        notes.append(ParsedNote(path=path, frontmatter_text=frontmatter_text, body=body))
    return notes


def _safe_vault_path(path: str) -> str:
    """Normalize and validate a path. Only allow topics/, vocabulary/, sessions/."""
    path = path.strip().lstrip("/")
    if not path.endswith(".md"):
        raise ValueError(f"non-md path: {path}")
    parts = path.split("/")
    if len(parts) != 2:
        raise ValueError(f"path must be folder/file.md: {path}")
    folder, name = parts
    if folder not in ("topics", "vocabulary", "sessions"):
        raise ValueError(f"folder must be topics/vocabulary/sessions: {path}")
    if any(c in name for c in ("..", "\\")):
        raise ValueError(f"invalid filename: {path}")
    return f"{folder}/{slugify(name[:-3])}.md"


def _parse_frontmatter(text: str) -> dict:
    import yaml

    if not text.strip():
        return {}
    try:
        data = yaml.safe_load(text) or {}
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _build_user_prompt(conversation_id: int, messages: list[Message]) -> str:
    today = date.today().isoformat()

    existing_topics = sorted({n.title for n in list_notes("topics")})
    existing_vocab = sorted({n.title for n in list_notes("vocabulary")})

    transcript_lines = []
    for m in messages:
        if m.role not in ("user", "assistant"):
            continue
        role = "Student" if m.role == "user" else "Tutor"
        transcript_lines.append(f"{role}: {m.content}")
        if m.role == "assistant" and m.corrections_json:
            for corr in m.corrections_json:
                transcript_lines.append(
                    f"  (correction: '{corr.get('original')}' → '{corr.get('fixed')}' — {corr.get('explanation_ru')})"
                )
    transcript = "\n".join(transcript_lines)

    return f"""You are curating an Obsidian-style markdown vault for an English-learning student.

Today: {today}
Conversation id: {conversation_id}

Existing topics in vault: {", ".join(existing_topics) if existing_topics else "(none)"}
Existing vocabulary in vault: {", ".join(existing_vocab) if existing_vocab else "(none)"}

Transcript:
{transcript}

# Your output format

Reply with one or more note blocks in EXACTLY this format (no extra text outside blocks):

<<<NOTE path="topics/<kebab-slug>.md">>>
---
type: topic
cefr: A1
created: {today}
updated: {today}
---

# Present Simple

Short body (Russian-explained for A1/A2 learners). Use [[wiki-links]] to other notes.
<<<END_NOTE>>>

<<<NOTE path="vocabulary/<kebab-slug>.md">>>
---
type: vocab
word: figure out
lemma: figure out
pos: phrasal_verb
cefr: B1
translation_ru: разобраться
created: {today}
---

# figure out

**Перевод:** разобраться, понять

> Example sentence.
> Перевод.
<<<END_NOTE>>>

<<<NOTE path="sessions/{today}-conv-{conversation_id}.md">>>
---
type: session
conversation_id: {conversation_id}
date: {today}
topics: [present-simple]
vocabulary: [figure-out]
---

# Session {today} — short title

## What we covered
- [[Present Simple]] — что именно практиковали.

## New vocabulary
- [[figure out]] — разобраться.

## Mistakes corrected
- "I goed" → "I went" — прошедшее время от irregular verb 'go'.

## Next steps
- Practice Past Simple irregular verbs.
<<<END_NOTE>>>

# Rules

1. Output EXACTLY ONE session note (`sessions/{today}-conv-{conversation_id}.md`).
2. For each NEW topic or vocabulary item that came up — but only if it's NOT already in the existing-lists above — output a separate note block. Don't duplicate existing notes.
3. Filenames: lowercase ASCII, kebab-case.
4. `[[wiki-links]]` should match the H1 title of the target note.
5. Bodies are written for A1–A2 learners: short, with Russian glosses for grammar terms.
6. Do not produce any other text outside the `<<<NOTE ...>>> ... <<<END_NOTE>>>` blocks.
"""


@dataclass
class SummarizerResult:
    new_note_paths: list[str]
    skipped_paths: list[str]
    raw_reply: str


async def summarize_conversation(
    conversation_id: int, messages: list[Message]
) -> SummarizerResult:
    user_prompt = _build_user_prompt(conversation_id, messages)
    system_prompt = (
        "You are a meticulous knowledge librarian for an English-learning student. "
        "Reply ONLY with note blocks in the specified format. No commentary, no markdown "
        "outside the blocks, no explanations."
    )
    raw = await claude_complete(system_prompt=system_prompt, user_message=user_prompt)

    parsed = _parse_blocks(raw)
    new_paths: list[str] = []
    skipped: list[str] = []

    today_iso = date.today().isoformat()

    for note in parsed:
        try:
            safe_path = _safe_vault_path(note.path)
        except ValueError:
            skipped.append(note.path)
            continue
        fm = _parse_frontmatter(note.frontmatter_text)
        if "created" not in fm:
            fm["created"] = today_iso
        if note.path.startswith("sessions/") and "date" not in fm:
            fm["date"] = today_iso
        try:
            saved = write_note(safe_path, fm, note.body)
            new_paths.append(saved.path)
        except (OSError, ValueError):
            skipped.append(note.path)

    return SummarizerResult(new_note_paths=new_paths, skipped_paths=skipped, raw_reply=raw)
