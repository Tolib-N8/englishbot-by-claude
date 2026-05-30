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

PHRASE_SYSTEM = (
    "You generate a short English sentence for a Russian-speaking learner to read aloud. "
    "Reply with ONLY the sentence — no quotes, no commentary, no JSON."
)


async def generate_phrase(level: str, focus: str | None = None) -> str:
    user = (
        f"Generate ONE English sentence for a learner at CEFR level {level}. "
        + (f"Target the sound or pattern: {focus}. " if focus else "")
        + "Length 6-12 words. Natural, useful in real speech."
    )
    try:
        reply = await claude_complete(system_prompt=PHRASE_SYSTEM, user_message=user)
        # Strip quotes/code-fences if any.
        return reply.strip().strip("`").strip("\"'").strip()
    except Exception:
        return "I would like a cup of coffee, please."
