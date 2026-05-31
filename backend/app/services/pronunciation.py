"""Score a pronunciation attempt by comparing target text to Whisper transcript.

Algorithm:
  - normalize both strings (lowercase, strip punctuation)
  - word-level Levenshtein alignment → per-word match / mismatch / missing / extra
  - overall score = matched_words / target_words
  - Claude generates a short Russian tip pointing at the worst word

No phoneme/IPA math — kept on purpose. Whisper transcribes what it actually
hears, so word-level matching already catches most pronunciation errors a
learner makes (e.g. "tree" vs "three").
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.anthropic_client import claude_complete

WORD_RE = re.compile(r"[a-z']+")


def _normalize(s: str) -> list[str]:
    return WORD_RE.findall(s.lower())


def _align(target: list[str], said: list[str]) -> list[dict]:
    """LCS-style alignment → per-target-word verdict.

    Each entry: {word, status: matched|missed|substituted, heard?}.
    """
    n, m = len(target), len(said)
    # dp[i][j] = length of LCS for target[:i] and said[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            if target[i] == said[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])

    # Walk back to reconstruct matches.
    matched: set[int] = set()  # indices in target that matched
    sub_heard: dict[int, str] = {}  # target index → word actually heard at same position
    i, j = n, m
    while i > 0 and j > 0:
        if target[i - 1] == said[j - 1]:
            matched.add(i - 1)
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # target[i-1] not in LCS → if there's any said[j-1..something] nearby, note it
            if j > 0:
                sub_heard.setdefault(i - 1, said[j - 1])
            i -= 1
        else:
            j -= 1

    out: list[dict] = []
    for idx, w in enumerate(target):
        if idx in matched:
            out.append({"word": w, "status": "matched"})
        else:
            entry = {"word": w, "status": "substituted" if idx in sub_heard else "missed"}
            if idx in sub_heard:
                entry["heard"] = sub_heard[idx]
            out.append(entry)
    return out


@dataclass
class PronunciationResult:
    transcript: str
    overall_score: float  # 0..1
    per_word: list[dict]
    tip_ru: str | None


async def _claude_tip(target: str, transcript: str, per_word: list[dict], score: float) -> str:
    if score >= 0.95:
        return "Отлично! Произношение почти безошибочное."

    problems = [w for w in per_word if w["status"] != "matched"]
    prob_summary = "; ".join(
        f"'{w['word']}'" + (f" → услышано '{w.get('heard', '')}'" if w.get("heard") else " (пропущено)")
        for w in problems[:5]
    )

    system = (
        "You are an English pronunciation coach helping a Russian-speaking learner. "
        "Reply ONLY with one short paragraph in Russian (2-3 sentences). Focus on the WORST 1-2 "
        "mistakes. Be concrete about which English sound to practice (e.g. /θ/, /æ/, /ð/, /ɜː/) "
        "and contrast with the closest Russian sound when useful."
    )
    user = (
        f"Target sentence: {target}\n"
        f"What Whisper heard:  {transcript}\n"
        f"Overall accuracy: {score:.0%}\n"
        f"Problem words: {prob_summary or '(none)'}\n\n"
        "Write the short Russian tip now."
    )
    try:
        reply = await claude_complete(system_prompt=system, user_message=user)
        return reply.strip().strip("`").strip()
    except Exception:
        return None


async def score_attempt(target: str, transcript: str) -> PronunciationResult:
    tgt = _normalize(target)
    said = _normalize(transcript)
    per_word = _align(tgt, said) if tgt else []
    matched = sum(1 for w in per_word if w["status"] == "matched")
    overall = matched / len(per_word) if per_word else 0.0
    tip = await _claude_tip(target, transcript, per_word, overall)
    return PronunciationResult(
        transcript=transcript,
        overall_score=overall,
        per_word=per_word,
        tip_ru=tip,
    )


# --- Practice phrase generator (Claude-driven) -------------------------------
#
# Phrase generation takes ~10 s per call. We hide that by keeping an in-memory
# pool: every request pops a ready phrase instantly and triggers a background
# refill when the pool runs low.

import asyncio  # noqa: E402

PHRASE_SYSTEM = (
    "You generate short English sentences for a Russian-speaking learner to read aloud. "
    "Reply with ONLY a JSON array of strings — no other text."
)

POOL_REFILL_AT = 3       # refill when fewer than this remain
POOL_TARGET = 8          # how many to ask Claude for at a time
_POOL_FALLBACK = "I would like a cup of coffee, please."

_pool: dict[tuple[str, str | None], list[str]] = {}
_pool_lock = asyncio.Lock()
_refilling: set[tuple[str, str | None]] = set()


async def _generate_batch(level: str, focus: str | None, count: int) -> list[str]:
    user = (
        f"Generate {count} different English sentences for a learner at CEFR level {level}. "
        + (f"Target the sound/pattern: {focus}. " if focus else "")
        + "Each sentence 6-12 words, natural, useful in real speech. "
        "Reply ONLY with a JSON array like: [\"sentence one\", \"sentence two\"]"
    )
    try:
        reply = await claude_complete(system_prompt=PHRASE_SYSTEM, user_message=user)
        # Try to extract the JSON array.
        text = reply.strip().strip("`").strip()
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return []
        import json

        data = json.loads(text[start : end + 1])
        if not isinstance(data, list):
            return []
        return [str(s).strip().strip("\"'").strip() for s in data if str(s).strip()]
    except Exception:
        return []


async def _refill(key: tuple[str, str | None]) -> None:
    level, focus = key
    if key in _refilling:
        return
    _refilling.add(key)
    try:
        batch = await _generate_batch(level, focus, POOL_TARGET)
        async with _pool_lock:
            _pool.setdefault(key, []).extend(batch)
    finally:
        _refilling.discard(key)


async def generate_phrase(level: str, focus: str | None = None) -> str:
    """Return a ready phrase from the pool, refilling in the background."""
    key = (level, focus)

    async with _pool_lock:
        bucket = _pool.setdefault(key, [])
        phrase = bucket.pop(0) if bucket else None
        need_refill = len(bucket) < POOL_REFILL_AT

    if need_refill:
        # Fire-and-forget background refill so this request stays fast.
        asyncio.create_task(_refill(key))

    if phrase is not None:
        return phrase

    # Cold start: pool was empty, fall back to a one-shot generation so the
    # very first call still returns a real phrase (slow path, ~10 s).
    batch = await _generate_batch(level, focus, POOL_TARGET)
    if batch:
        async with _pool_lock:
            _pool.setdefault(key, []).extend(batch[1:])
        return batch[0]
    return _POOL_FALLBACK
