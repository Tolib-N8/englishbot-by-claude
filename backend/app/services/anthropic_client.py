"""Claude client using Claude Agent SDK (Pro/Max subscription, no API key needed).

The SDK spawns the `claude` CLI under the hood and uses the OAuth session
created by `claude /login` (stored in ~/.claude/). This means the backend
must be running on the same host (or with ~/.claude/ mounted) and that
Claude Code is installed and authenticated.

We don't use the streaming `query()` API directly here because the SDK is
session-oriented; instead we use a single-turn helper for each request,
which is the right shape for our chat-per-turn flow.
"""
from collections.abc import AsyncIterator

from claude_agent_sdk import ClaudeAgentOptions, query


async def claude_stream(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> AsyncIterator[str]:
    """Yield assistant text chunks as they arrive."""
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        # We do not need Claude Code's filesystem / shell tools for tutoring.
        allowed_tools=[],
        permission_mode="default",
    )
    async for msg in query(prompt=user_message, options=options):
        # The SDK yields AssistantMessage, UserMessage, ResultMessage objects.
        # We forward only assistant text blocks.
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
    """Collect a non-streamed full reply."""
    parts: list[str] = []
    async for chunk in claude_stream(
        system_prompt=system_prompt, user_message=user_message, model=model
    ):
        parts.append(chunk)
    return "".join(parts)
