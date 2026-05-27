"""Claude client using Claude Agent SDK (Pro/Max subscription, no API key needed).

The SDK spawns the `claude` CLI under the hood and uses the OAuth session
created by `claude /login` (stored in ~/.claude/). Backend must run on the
same host where Claude Code is installed and authenticated.

We never grant the SDK any tools — Claude is purely a text generator here.
File writes (e.g. vault notes) happen in Python after parsing Claude's
text output, so the user retains full visibility and control.
"""
from collections.abc import AsyncIterator

from claude_agent_sdk import ClaudeAgentOptions, query


def _make_options(*, system_prompt: str, model: str | None) -> ClaudeAgentOptions:
    kwargs: dict = {
        "system_prompt": system_prompt,
        "allowed_tools": [],
        "permission_mode": "default",
    }
    if model:
        kwargs["model"] = model
    return ClaudeAgentOptions(**kwargs)


async def claude_stream(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> AsyncIterator[str]:
    """Yield assistant text chunks as they arrive."""
    options = _make_options(system_prompt=system_prompt, model=model)
    async for msg in query(prompt=user_message, options=options):
        content = getattr(msg, "content", None)
        if not content:
            continue
        for block in content:
            text = getattr(block, "text", None)
            if text:
                yield text


async def claude_complete(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> str:
    parts: list[str] = []
    async for chunk in claude_stream(
        system_prompt=system_prompt, user_message=user_message, model=model
    ):
        parts.append(chunk)
    return "".join(parts)
