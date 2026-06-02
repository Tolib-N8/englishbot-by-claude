"""IELTS Writing — prompt generation + criterion-based grading.

Two task types supported:
  - task1_academic  (describe a chart/graph/diagram, ≥150 words, ~20 min)
  - task2           (essay on an argument/opinion, ≥250 words, ~40 min)

Grader returns the official 4 IELTS Writing criteria with band scores 0–9,
Russian commentary, an overall band, inline corrections, and a Russian tip.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.services.anthropic_client import claude_complete

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)

WORD_RE = re.compile(r"\b[\w'-]+\b")

ALLOWED_TASKS = {"task1_academic", "task2"}


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


# --- Prompt generation -------------------------------------------------------

PROMPT_SYSTEM = (
    "You write IELTS Writing exam prompts for a Russian-speaking learner. "
    "Reply ONLY with a fenced JSON block. No commentary."
)


def _build_prompt_request(task_type: str, level: str) -> str:
    if task_type == "task1_academic":
        guide = (
            "Generate an IELTS Academic Writing Task 1 prompt: describe a graph, "
            "chart, table, process, or map. The learner has 20 minutes and must "
            "write at least 150 words. Describe the visual in WORDS only — give "
            "concrete numbers and trends the learner is supposed to summarise."
        )
        min_words = 150
    else:  # task2
        guide = (
            "Generate an IELTS Writing Task 2 essay question. The learner has 40 "
            "minutes and must write at least 250 words. Pick a clear opinion / "
            "discuss / problem-solution / two-views topic appropriate for the level."
        )
        min_words = 250
    return f"""{guide}

CEFR level: {level}.

Reply with ONLY this JSON:

```json
{{
  "prompt_en": "the IELTS prompt text (English) — include data details if Task 1",
  "prompt_ru": "краткое пояснение задания на русском (1-2 предложения)",
  "min_words": {min_words}
}}
```"""


@dataclass
class WritingPrompt:
    prompt_en: str
    prompt_ru: str | None
    min_words: int


def _extract_json(text: str) -> dict[str, Any] | None:
    m = JSON_BLOCK_RE.search(text)
    candidate = m.group(1) if m else text
    for attempt in (candidate, text[text.find("{") : text.rfind("}") + 1] if "{" in text else ""):
        if not attempt:
            continue
        try:
            data = json.loads(attempt)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None


async def generate_writing_prompt(task_type: str, level: str) -> WritingPrompt:
    if task_type not in ALLOWED_TASKS:
        raise ValueError(f"task_type must be one of {ALLOWED_TASKS}")
    reply = await claude_complete(
        system_prompt=PROMPT_SYSTEM,
        user_message=_build_prompt_request(task_type, level),
    )
    data = _extract_json(reply) or {}
    return WritingPrompt(
        prompt_en=str(data.get("prompt_en") or "").strip()
        or "Write about a memorable journey you took. (fallback)",
        prompt_ru=(str(data["prompt_ru"]).strip() if data.get("prompt_ru") else None),
        min_words=int(data.get("min_words") or (150 if task_type == "task1_academic" else 250)),
    )


# --- Grading -----------------------------------------------------------------

GRADER_SYSTEM = (
    "You are an experienced IELTS Writing examiner. You grade honestly and "
    "ground every comment in concrete evidence from the learner's own text. "
    "Bands run 0-9 in 0.5 increments. Reply ONLY with the requested JSON block."
)


def _build_grader_prompt(task_type: str, prompt_en: str, text: str, min_words: int) -> str:
    wc = count_words(text)
    is_task1 = task_type == "task1_academic"
    return f"""Grade this IELTS {"Academic Writing Task 1" if is_task1 else "Writing Task 2"} answer.

PROMPT (the question the learner was asked):
{prompt_en}

LEARNER'S ANSWER ({wc} words; minimum is {min_words}):
\"\"\"{text}\"\"\"

Reply with ONLY this JSON:

```json
{{
  "overall_band": "5.5",
  "criteria": [
    {{"name": "{"Task Achievement" if is_task1 else "Task Response"}", "band": "5.5", "comment_ru": "1-2 предложения, что хорошо/плохо, конкретно."}},
    {{"name": "Coherence and Cohesion", "band": "6.0", "comment_ru": "..."}},
    {{"name": "Lexical Resource", "band": "5.0", "comment_ru": "..."}},
    {{"name": "Grammatical Range and Accuracy", "band": "5.0", "comment_ru": "..."}}
  ],
  "corrections": [
    {{"original": "exact substring from the learner's text", "fixed": "corrected version", "explanation_ru": "коротко по-русски"}}
  ],
  "tip_ru": "1-3 предложения: ГЛАВНОЕ что улучшить для следующего раза, на русском."
}}
```

Rules:
- overall_band = arithmetic mean of the 4 criteria, rounded to the nearest 0.5 (IELTS rounding).
- 3-8 corrections of the most impactful errors. The `original` MUST be an exact substring of the learner's text (case-sensitive) so the UI can highlight it.
- If under-length, dock Task Achievement / Task Response accordingly.
- Be honest about a low band on a weak answer. Do not inflate.
- Russian comments only; quotes stay in English."""


@dataclass
class WritingGrade:
    overall_band: str
    criteria: list[dict]
    corrections: list[dict]
    tip_ru: str | None


async def grade_essay(task_type: str, prompt_en: str, text: str, min_words: int) -> WritingGrade:
    if task_type not in ALLOWED_TASKS:
        raise ValueError(f"task_type must be one of {ALLOWED_TASKS}")
    reply = await claude_complete(
        system_prompt=GRADER_SYSTEM,
        user_message=_build_grader_prompt(task_type, prompt_en, text, min_words),
    )
    data = _extract_json(reply) or {}
    return WritingGrade(
        overall_band=str(data.get("overall_band") or "0").strip(),
        criteria=list(data.get("criteria") or []),
        corrections=list(data.get("corrections") or []),
        tip_ru=(str(data["tip_ru"]).strip() if data.get("tip_ru") else None),
    )
