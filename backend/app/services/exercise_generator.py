"""Generate grammar exercises with Claude (text-only, no tools).

Claude returns a fenced JSON block; Python parses it. Same safe pattern as
the vocab extractor and session summarizer.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.services.anthropic_client import claude_complete

JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)

ALLOWED_TYPES = {"fill_blank", "mcq", "translate_ru_en", "translate_en_ru"}

GENERATOR_SYSTEM = (
    "You are an English grammar exercise author for a Russian-speaking learner preparing "
    "for IELTS. You write clear, level-appropriate exercises with concise Russian explanations. "
    "Reply ONLY with the requested JSON block — no commentary, no tools."
)


def _build_prompt(topic: str, level: str, count: int, types: list[str]) -> str:
    type_list = ", ".join(types)
    return f"""Create {count} English grammar exercises on the topic "{topic}" for a
Russian-speaking learner at CEFR level {level} (IELTS prep).

Mix these exercise types: {type_list}.

Reply with ONLY this fenced JSON block (no text before/after):

```json
{{
  "exercises": [
    {{
      "type": "fill_blank",
      "prompt": "She ___ to school every day.",
      "prompt_ru": null,
      "answer": "goes",
      "alternatives": [],
      "choices": null,
      "explanation_ru": "Present Simple, 3-е лицо ед.ч.: глагол + -s."
    }},
    {{
      "type": "mcq",
      "prompt": "I ___ TV right now.",
      "prompt_ru": null,
      "answer": "am watching",
      "alternatives": [],
      "choices": ["watch", "am watching", "watched", "watches"],
      "explanation_ru": "Действие сейчас → Present Continuous: am/is/are + V-ing."
    }},
    {{
      "type": "translate_ru_en",
      "prompt": "Translate to English.",
      "prompt_ru": "Я обычно играю в футбол по выходным.",
      "answer": "I usually play football at the weekend.",
      "alternatives": ["I usually play football on weekends."],
      "choices": null,
      "explanation_ru": "Привычка → Present Simple; 'usually' перед глаголом."
    }}
  ]
}}
```

Rules:
- type must be one of: {type_list}.
- fill_blank: put exactly one blank as "___" in the English prompt; answer is the missing word(s).
- mcq: provide 4 plausible choices; answer must be one of them verbatim.
- translate_ru_en: prompt_ru is the Russian sentence; answer is a natural English translation;
  add 1-3 acceptable variants in alternatives.
- translate_en_ru: prompt is the English sentence; answer is the Russian translation.
- explanation_ru: one short sentence in Russian explaining the rule.
- Keep vocabulary at level {level}. No exercise should depend on words above the level.
- No text outside the JSON block."""


def _extract(reply: str) -> dict[str, Any] | None:
    m = JSON_BLOCK_RE.search(reply)
    candidate = m.group(1) if m else reply
    for attempt in (candidate, reply[reply.find("{") : reply.rfind("}") + 1] if "{" in reply else ""):
        if not attempt:
            continue
        try:
            data = json.loads(attempt)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None


def _clean(item: dict) -> dict | None:
    etype = str(item.get("type") or "").strip()
    if etype not in ALLOWED_TYPES:
        return None
    prompt = str(item.get("prompt") or "").strip()
    answer = str(item.get("answer") or "").strip()
    if not prompt or not answer:
        return None
    if etype == "mcq":
        choices = item.get("choices") or []
        if not isinstance(choices, list) or answer not in choices:
            return None
    return {
        "type": etype,
        "prompt": prompt,
        "prompt_ru": (str(item["prompt_ru"]).strip() if item.get("prompt_ru") else None),
        "answer": answer,
        "alternatives": [str(a).strip() for a in (item.get("alternatives") or []) if str(a).strip()],
        "choices": item.get("choices") if etype == "mcq" else None,
        "explanation_ru": (str(item["explanation_ru"]).strip() if item.get("explanation_ru") else None),
    }


async def generate_exercises(
    topic: str, level: str, count: int, types: list[str] | None = None
) -> list[dict]:
    types = [t for t in (types or list(ALLOWED_TYPES)) if t in ALLOWED_TYPES] or list(ALLOWED_TYPES)
    reply = await claude_complete(
        system_prompt=GENERATOR_SYSTEM,
        user_message=_build_prompt(topic, level, count, types),
    )
    data = _extract(reply) or {}
    out: list[dict] = []
    for item in data.get("exercises", []):
        if isinstance(item, dict):
            cleaned = _clean(item)
            if cleaned:
                out.append(cleaned)
    return out
