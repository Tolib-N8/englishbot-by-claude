"""Extract vocabulary from an English text via Claude (Agent SDK).

Without API-style tool-use, we ask Claude for a JSON reply and parse it.
"""
import json
import re
from typing import Any

from app.services.anthropic_client import claude_complete
from app.services.prompts import VOCAB_EXTRACTOR_SYSTEM


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any] | None:
    """Find the first JSON object in the reply."""
    m = JSON_BLOCK_RE.search(text)
    candidate = m.group(1) if m else text
    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    # try to grab a {...} substring
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
    return None


async def extract_vocabulary(text: str) -> list[dict[str, Any]]:
    reply = await claude_complete(
        system_prompt=VOCAB_EXTRACTOR_SYSTEM,
        user_message=text,
    )
    data = _extract_json(reply)
    if not data:
        return []
    items = data.get("items", [])
    return [i for i in items if isinstance(i, dict) and i.get("word_en")]
