"""Output guardrail: reject analyst messages that quote numeric facts without a
backing tool call on this turn.

This is a lightweight heuristic that catches the most common hallucination —
a made-up closing price. It is not a proof system; the deeper enforcement is
the Verifier agent in the swarm.
"""

from __future__ import annotations

import re
from typing import Any

from agents import (
    GuardrailFunctionOutput,
    RunContextWrapper,
    output_guardrail,
)

# Numbers like 1,234.56 / 98.4% / 24,500 / ₹512.20
_NUMBER_RE = re.compile(r"(?<![A-Za-z_])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")


@output_guardrail
async def tool_first_numbers(
    ctx: RunContextWrapper[Any], agent, output: Any,
) -> GuardrailFunctionOutput:
    """Flag numeric content when no tools were called on this run."""
    text = getattr(output, "markdown", None) or getattr(output, "message_markdown", None)
    if not isinstance(text, str):
        text = str(output)

    numbers = _NUMBER_RE.findall(text)
    if not numbers:
        return GuardrailFunctionOutput(output_info={"numbers": []}, tripwire_triggered=False)

    used_tools = []
    # `ctx.usage` / `ctx.context` don't directly expose tool history in a stable
    # way across SDK versions. Callers should attach a `tool_calls` list to the
    # RunContext's `context` dict; we treat missing as "unknown" and allow.
    raw_ctx = getattr(ctx, "context", None)
    if isinstance(raw_ctx, dict):
        used_tools = raw_ctx.get("tool_calls", []) or []

    if not used_tools:
        # Strict mode is the Verifier's job; here we only hard-trip when the
        # message contains what looks like a Rupee price quote.
        looks_like_price = any("₹" in text or re.search(r"\b\d+\.\d{2}\b", text) for _ in [0])
        return GuardrailFunctionOutput(
            output_info={"numbers": numbers, "reason": "no tool calls on this turn"},
            tripwire_triggered=looks_like_price,
        )

    return GuardrailFunctionOutput(
        output_info={"numbers": numbers, "tool_calls": used_tools},
        tripwire_triggered=False,
    )
