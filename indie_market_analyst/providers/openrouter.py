"""OpenRouter provider, using the SDK's LiteLLM extension.

LiteLLM's OpenRouter route expects the model string `openrouter/<slug>` and reads
`OPENROUTER_API_KEY` from env automatically. We pass it explicitly for clarity,
and inject the OpenRouter referer/title headers via LiteLLM's `extra_headers`
through env vars that the OpenRouter docs recognize.
"""

from __future__ import annotations

import os

from agents.extensions.models.litellm_model import LitellmModel


def make_openrouter_model(slug: str) -> LitellmModel:
    """Return a `LitellmModel` routed through OpenRouter.

    Args:
        slug: e.g. ``"anthropic/claude-sonnet-4"`` or ``"openai/gpt-4o-mini"``.
              The ``openrouter/`` prefix is added automatically.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and fill it in."
        )

    # LiteLLM reads OR_SITE_URL / OR_APP_NAME for OpenRouter analytics headers.
    os.environ.setdefault(
        "OR_SITE_URL", os.environ.get("OPENROUTER_APP_URL", "http://localhost:8000")
    )
    os.environ.setdefault(
        "OR_APP_NAME", os.environ.get("OPENROUTER_APP_TITLE", "indie-market-analyst")
    )

    model_id = slug if slug.startswith("openrouter/") else f"openrouter/{slug}"
    return LitellmModel(model=model_id, base_url=base_url, api_key=api_key)
