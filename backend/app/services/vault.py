"""Read/write the Obsidian-style markdown vault.

The vault is the shared persistent memory between the learner and Claude.
Filesystem is the source of truth — we don't index notes in the DB.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from app.config import PROJECT_ROOT

VAULT_DIR = PROJECT_ROOT / "vault"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")


@dataclass
class Note:
    path: str  # vault-relative, forward-slash, e.g. "topics/present-simple.md"
    folder: str  # "topics" | "vocabulary" | "sessions" | "" for root
    name: str  # stem without extension, e.g. "present-simple"
    frontmatter: dict
    body: str

    @property
    def title(self) -> str:
        # First H1 in body, else the file stem
        for line in self.body.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return self.name.replace("-", " ").capitalize()

    def links(self) -> list[str]:
        return [m.group(1).strip() for m in WIKI_LINK_RE.finditer(self.body)]


def _parse(raw: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
    body = raw[m.end():]
    return fm, body


def _serialize(frontmatter: dict, body: str) -> str:
    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    body = body.lstrip("\n")
    return f"---\n{fm}\n---\n\n{body}"


def _safe_rel(path: str) -> Path:
    """Reject paths that escape the vault."""
    if not path:
        raise ValueError("empty path")
    rel = Path(path)
    if rel.is_absolute() or any(part == ".." for part in rel.parts):
        raise ValueError("invalid path")
    if rel.suffix.lower() != ".md":
        raise ValueError("only .md files are allowed")
    return rel


def ensure_vault() -> None:
    for sub in ("topics", "vocabulary", "sessions"):
        (VAULT_DIR / sub).mkdir(parents=True, exist_ok=True)


def list_notes(folder: str | None = None) -> list[Note]:
    ensure_vault()
    notes: list[Note] = []
    targets: Iterable[Path]
    if folder:
        targets = (VAULT_DIR / folder).rglob("*.md")
    else:
        targets = VAULT_DIR.rglob("*.md")
    for p in targets:
        try:
            note = read_note_by_path(p.relative_to(VAULT_DIR).as_posix())
            notes.append(note)
        except (OSError, ValueError):
            continue
    notes.sort(key=lambda n: (n.folder, n.name))
    return notes


def read_note_by_path(rel_path: str) -> Note:
    rel = _safe_rel(rel_path)
    full = (VAULT_DIR / rel).resolve()
    if not full.is_relative_to(VAULT_DIR.resolve()):
        raise ValueError("path escapes vault")
    if not full.exists():
        raise FileNotFoundError(rel_path)
    raw = full.read_text(encoding="utf-8")
    fm, body = _parse(raw)
    parts = rel.parts
    folder = parts[0] if len(parts) > 1 else ""
    return Note(
        path=rel.as_posix(),
        folder=folder,
        name=rel.stem,
        frontmatter=fm,
        body=body,
    )


def write_note(rel_path: str, frontmatter: dict, body: str) -> Note:
    ensure_vault()
    rel = _safe_rel(rel_path)
    full = (VAULT_DIR / rel).resolve()
    if not full.is_relative_to(VAULT_DIR.resolve()):
        raise ValueError("path escapes vault")
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(_serialize(frontmatter, body), encoding="utf-8")
    return read_note_by_path(rel.as_posix())


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "untitled"


def list_topic_names() -> list[str]:
    """Return human titles of every topic note."""
    return [n.title for n in list_notes("topics")]


def recent_sessions(limit: int = 2) -> list[Note]:
    sessions = list_notes("sessions")
    sessions.sort(
        key=lambda n: str(n.frontmatter.get("date", "")) or n.name,
        reverse=True,
    )
    return sessions[:limit]


def memory_snapshot(max_session_chars: int = 1200) -> str:
    """Compact summary of what the learner has covered so far.

    Returned as a single block of text suitable to prepend to a chat prompt.
    Empty string if the vault has nothing yet.
    """
    topics = list_topic_names()
    sessions = recent_sessions(2)
    if not topics and not sessions:
        return ""

    lines: list[str] = ["[Learner's vault — what we have already covered]"]
    if topics:
        lines.append("Topics: " + ", ".join(topics))
    for s in sessions:
        date = s.frontmatter.get("date", "")
        title = s.title
        excerpt = s.body.strip()
        if len(excerpt) > max_session_chars:
            excerpt = excerpt[:max_session_chars] + "…"
        lines.append("")
        lines.append(f"Session [{date}] — {title}")
        lines.append(excerpt)
    lines.append("[End of vault snapshot]")
    return "\n".join(lines)
