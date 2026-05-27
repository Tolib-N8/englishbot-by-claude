"""Parse the trailing ```corrections JSON block from a tutor reply."""
import json
import re

CORRECTION_BLOCK_RE = re.compile(
    r"```corrections\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE
)


def split_corrections(text: str) -> tuple[str, list[dict] | None]:
    """Return (clean_reply, corrections | None)."""
    match = CORRECTION_BLOCK_RE.search(text)
    if not match:
        return text.strip(), None

    body = match.group(1).strip()
    try:
        parsed = json.loads(body)
        if not isinstance(parsed, list):
            return text.strip(), None
    except json.JSONDecodeError:
        return text.strip(), None

    cleaned = CORRECTION_BLOCK_RE.sub("", text).rstrip()
    return cleaned, parsed
