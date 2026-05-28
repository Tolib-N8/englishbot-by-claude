"""Grade exercise answers.

fill_blank / mcq → exact match against answer + alternatives (normalized), local.
translate_* → lenient grading by Claude (accepts synonyms, minor article slips).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.models.exercise import GrammarExercise
from app.services.anthropic_client import claude_complete

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)

GRADER_SYSTEM = (
    "You grade a Russian-speaking beginner's English translation generously but honestly. "
    "Reply ONLY with the requested JSON."
)


@dataclass
class GradeResult:
    is_correct: bool
    feedback_ru: str | None


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s]+", " ", s)
    s = re.sub(r"[.,!?;:\"'`]+$", "", s)  # trailing punctuation
    return s


def _local_match(user: str, answer: str, alternatives: list[str]) -> bool:
    candidates = {_normalize(answer)} | {_normalize(a) for a in alternatives}
    return _normalize(user) in candidates


async def _grade_translation(ex: GrammarExercise, user_answer: str) -> GradeResult:
    if ex.type == "translate_ru_en":
        source_label = "Russian original"
        source = ex.prompt_ru or ex.prompt
    else:  # translate_en_ru
        source_label = "English original"
        source = ex.prompt
    prompt = f"""Grade this translation generously (beginner level, IELTS prep).

{source_label}: {source}
Reference answer: {ex.answer}
Acceptable variants: {", ".join(ex.alternatives_json or []) or "(none)"}
Student wrote: {user_answer}

Accept synonyms, alternate word order, contractions, and minor article slips (a/the).
Mark INCORRECT for wrong tense, wrong verb, or changed meaning.

Reply ONLY with:
```json
{{"is_correct": true, "feedback_ru": "1-2 предложения обратной связи на русском"}}
```"""
    reply = await claude_complete(system_prompt=GRADER_SYSTEM, user_message=prompt)
    m = JSON_BLOCK_RE.search(reply)
    raw = m.group(1) if m else reply[reply.find("{") : reply.rfind("}") + 1]
    try:
        data = json.loads(raw)
        return GradeResult(
            is_correct=bool(data.get("is_correct")),
            feedback_ru=(str(data["feedback_ru"]) if data.get("feedback_ru") else None),
        )
    except (json.JSONDecodeError, ValueError):
        # Fallback to a lenient local check if Claude's reply is unparseable.
        ok = _local_match(user_answer, ex.answer, ex.alternatives_json or [])
        return GradeResult(is_correct=ok, feedback_ru=None)


async def grade_attempt(ex: GrammarExercise, user_answer: str) -> GradeResult:
    if ex.type in ("fill_blank", "mcq"):
        ok = _local_match(user_answer, ex.answer, ex.alternatives_json or [])
        feedback = None if ok else f"Правильный ответ: {ex.answer}"
        return GradeResult(is_correct=ok, feedback_ru=feedback)
    return await _grade_translation(ex, user_answer)
