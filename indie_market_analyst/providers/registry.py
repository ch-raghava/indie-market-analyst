"""Per-role model selection driven by ``config/models.yaml``.

Roles map to ``agent_name`` strings used in swarm YAML. A role-specific override
wins; otherwise ``default`` is used.
"""

from __future__ import annotations

import os

from agents import Model

from .openrouter import make_openrouter_model


def slug_for_role(role: str) -> str:
    """Env-only model selection. ``MODEL_<ROLE>`` per role, ``MODEL_DEFAULT`` fallback.

    No YAML fallback, no hardcoded default — this prevents accidentally paying
    for a non-free model. Raises if neither env var is set so the user notices.
    """
    key = f"MODEL_{role.upper()}"
    slug = os.getenv(key) or os.getenv("MODEL_DEFAULT")
    if not slug:
        raise RuntimeError(
            f"No model configured for role '{role}'. "
            f"Set {key} or MODEL_DEFAULT in your .env."
        )
    return slug


def model_for_role(role: str) -> Model:
    return make_openrouter_model(slug_for_role(role))
