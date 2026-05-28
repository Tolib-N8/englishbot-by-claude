"""Honest CEFR / IELTS assessment of the learner's written English.

We collect everything the learner has actually written (their user-role
messages) and ask Claude to assess it against CEFR + IELTS writing
descriptors. The output is structured JSON we parse and store.

Honesty constraints baked into the prompt:
  - This is based ONLY on written chat production — not a full 4-skill IELTS
    (no Listening/Reading; Speaking only loosely proxied). Confidence must
    reflect the (usually small) sample size.
  - Estimate must be evidence-based: quote the learner's own sentences.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.services.anthropic_client import claude_complete

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)

ASSESSOR_SYSTEM = """You are a certified IELTS examiner and CEFR assessor. You assess a learner's
WRITTEN English production honestly and conservatively. You never inflate scores to be
encouraging. You ground every judgement in evidence from the learner's own text.

Important honesty rules:
- You are seeing ONLY the learner's written chat messages — not a real IELTS exam.
  You CANNOT assess Listening or Reading, and Speaking only very loosely. Say so.
- If the sample is small or mostly trivial, set confidence to "low" and say the
  estimate is provisional.
- Use the official CEFR↔IELTS mapping:
    IELTS <4.0 ≈ A1–A2 ; 4.0–5.0 ≈ B1 ; 5.5–6.5 ≈ B2 ; 7.0–8.0 ≈ C1 ; 8.5–9.0 ≈ C2.
- Judge against IELTS Writing criteria adapted to chat: Grammatical Range & Accuracy,
  Lexical Resource, Coherence & Cohesion, and Task/Idea development.
- Be specific and actionable. Comments and feedback in RUSSIAN; quotes stay in English."""


def _build_prompt(samples: list[str]) -> str:
    joined = "\n".join(f"- {s}" for s in samples)
    return f"""Assess this learner's written English. These are all the English sentences they
have produced in chat (Russian-only messages were filtered out):

{joined}

Reply with ONLY a fenced JSON block in EXACTLY this shape:

```json
{{
  "cefr_level": "B1",
  "ielts_band": "5.0",
  "confidence": "low",
  "summary_ru": "2-3 предложения: общий уровень и насколько оценка надёжна (учитывая объём данных).",
  "skills": [
    {{"name": "Grammatical Range & Accuracy", "cefr": "B1", "ielts": "5.0", "comment_ru": "..."}},
    {{"name": "Lexical Resource", "cefr": "A2", "ielts": "4.5", "comment_ru": "..."}},
    {{"name": "Coherence & Cohesion", "cefr": "B1", "ielts": "5.0", "comment_ru": "..."}},
    {{"name": "Task / Idea Development", "cefr": "B1", "ielts": "5.0", "comment_ru": "..."}}
  ],
  "strengths": ["сильная сторона на русском", "..."],
  "weaknesses": ["слабое место на русском", "..."],
  "next_steps": ["что конкретно делать чтобы поднять балл", "..."],
  "evidence": [
    {{"quote": "I have 25 years old", "issue_ru": "калька с русского; возраст через 'to be': I am 25."}}
  ]
}}
```

Rules:
- cefr_level is the OVERALL level (one of A1, A2, B1, B2, C1, C2).
- ielts_band is a single number like "5.5" reflecting WRITTEN production only.
- 3-6 evidence items quoting the learner's actual sentences (good or bad).
- confidence: "low" | "medium" | "high" — be honest about the sample size.
- No text outside the JSON block."""


@dataclass
class AssessmentResult:
    cefr_level: str
    ielts_band: str | None
    confidence: str
    summary_ru: str
    skills: list[dict]
    strengths: list[str]
    weaknesses: list[str]
    next_steps: list[str]
    evidence: list[dict]
    based_on_messages: int
    based_on_words: int


def _looks_english(text: str) -> bool:
    """Heuristic: keep messages that are mostly Latin letters (the learner's English)."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 3:
        return False
    latin = sum(1 for c in letters if "a" <= c.lower() <= "z")
    return latin / len(letters) >= 0.6


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


async def assess_writing(user_messages: list[str]) -> AssessmentResult:
    samples = [m.strip() for m in user_messages if _looks_english(m)]
    word_count = sum(len(s.split()) for s in samples)

    if not samples:
        return AssessmentResult(
            cefr_level="A1",
            ielts_band=None,
            confidence="low",
            summary_ru="Пока нет английских сообщений для оценки. Пообщайся в чате на английском, потом оцени уровень.",
            skills=[],
            strengths=[],
            weaknesses=[],
            next_steps=["Напиши хотя бы несколько предложений на английском в чате."],
            evidence=[],
            based_on_messages=0,
            based_on_words=0,
        )

    reply = await claude_complete(
        system_prompt=ASSESSOR_SYSTEM,
        user_message=_build_prompt(samples),
    )
    data = _extract_json(reply) or {}

    return AssessmentResult(
        cefr_level=str(data.get("cefr_level") or "A1"),
        ielts_band=(str(data["ielts_band"]) if data.get("ielts_band") else None),
        confidence=str(data.get("confidence") or "low"),
        summary_ru=str(data.get("summary_ru") or ""),
        skills=list(data.get("skills") or []),
        strengths=list(data.get("strengths") or []),
        weaknesses=list(data.get("weaknesses") or []),
        next_steps=list(data.get("next_steps") or []),
        evidence=list(data.get("evidence") or []),
        based_on_messages=len(samples),
        based_on_words=word_count,
    )
