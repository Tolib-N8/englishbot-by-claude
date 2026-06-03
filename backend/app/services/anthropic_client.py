"""Claude client using Claude Agent SDK (Pro/Max subscription, no API key needed).

The SDK spawns the `claude` CLI under the hood and uses the OAuth session
created by `claude /login` (stored in ~/.claude/). Backend must run on the
same host where Claude Code is installed and authenticated.

We never grant the SDK any tools — Claude is purely a text generator here.
File writes (e.g. vault notes) happen in Python after parsing Claude's
text output, so the user retains full visibility and control.

## Robustness against the SDK's "success" error
The CLI sometimes exits with a non-zero code AFTER successfully streaming
the answer back. The SDK then raises Exception("...error result: success").
We collect the streamed text into a buffer; if that exception fires but
the buffer already has meaningful content, we return it (the answer was
fine, only the wrapper exit code was wrong). On true failures (no text
yet), we retry up to 2 more times before giving up.
"""
import asyncio
import logging
from collections.abc import AsyncIterator

from claude_agent_sdk import ClaudeAgentOptions, query

log = logging.getLogger(__name__)

# When the streamed text is at least this long, we consider it a real
# answer and ignore a trailing "success" error from the CLI wrapper.
_MIN_USABLE_LEN = 80


def _make_options(*, system_prompt: str, model: str | None) -> ClaudeAgentOptions:
    kwargs: dict = {
        "system_prompt": system_prompt,
        "allowed_tools": [],
        "permission_mode": "default",
    }
    if model:
        kwargs["model"] = model
    return ClaudeAgentOptions(**kwargs)


def _is_success_error(exc: BaseException) -> bool:
    """Detect the SDK's spurious 'success' result error."""
    s = str(exc)
    return "error result: success" in s or s.strip().lower() == "success"


async def claude_stream(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> AsyncIterator[str]:
    """Yield assistant text chunks as they arrive.

    Note: callers that need crash-safety against the SDK's spurious
    "success" error should use `claude_complete` instead, which collects
    the stream and recovers the buffered text.
    """
    options = _make_options(system_prompt=system_prompt, model=model)
    async for msg in query(prompt=user_message, options=options):
        content = getattr(msg, "content", None)
        if not content:
            continue
        for block in content:
            text = getattr(block, "text", None)
            if text:
                yield text


async def _claude_complete_once(
    *, system_prompt: str, user_message: str, model: str | None
) -> str:
    """One attempt at a non-streamed completion. May raise."""
    parts: list[str] = []
    try:
        async for chunk in claude_stream(
            system_prompt=system_prompt, user_message=user_message, model=model
        ):
            parts.append(chunk)
    except Exception as exc:
        joined = "".join(parts)
        if _is_success_error(exc) and len(joined) >= _MIN_USABLE_LEN:
            log.warning(
                "Claude CLI exited non-zero with spurious 'success' but %d "
                "chars were already streamed — using buffered text.",
                len(joined),
            )
            return joined
        raise
    return "".join(parts)


async def claude_complete(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    max_retries: int = 2,
) -> str:
    """Robust non-streamed completion with retries on transient SDK errors."""
    last_exc: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            return await _claude_complete_once(
                system_prompt=system_prompt, user_message=user_message, model=model
            )
        except Exception as exc:
            last_exc = exc
            log.warning(
                "Claude attempt %d/%d failed: %s",
                attempt + 1,
                max_retries + 1,
                exc,
            )
            if attempt < max_retries:
                # Small backoff so we don't slam the local CLI.
                await asyncio.sleep(0.6 * (attempt + 1))
    assert last_exc is not None
    raise last_exc
