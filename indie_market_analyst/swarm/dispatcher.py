"""Build a live `Agent` graph from a YAML `TeamSpec`.

We construct each sub-agent first (leaf-up), then attach handoffs. An agent's
`output_type` string is resolved via `importlib.import_module`.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from agents import Agent, handoff

from ..providers.registry import model_for_role
from ..skills.registry import discover as discover_skills
from ..tools.registry import select as select_tools
from .topology import AgentSpec, TeamSpec, load_team

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "swarm"


def _resolve_output_type(dotted: str | None) -> Any | None:
    if not dotted:
        return None
    mod, _, cls = dotted.rpartition(".")
    return getattr(importlib.import_module(mod), cls)


def _instructions_for(spec: AgentSpec) -> str:
    parts = [spec.instructions.strip()] if spec.instructions else []
    skills = discover_skills()
    for s_name in spec.skills:
        skill = skills.get(s_name)
        if skill:
            parts.append(f"\n\n--- Skill: {skill.name} ---\n{skill.instructions}")
    return "\n".join(parts).strip() or "You are a specialist agent."


def build_team(team: TeamSpec) -> Agent:
    """Return the root (entry) `Agent` with its handoff graph wired."""
    agents_by_name: dict[str, Agent] = {}

    # Build leaves first so parents can reference them
    ordered = sorted(team.agents, key=lambda a: len(a.handoffs))
    for spec in ordered:
        agents_by_name[spec.name] = Agent(
            name=spec.name,
            instructions=_instructions_for(spec),
            model=model_for_role(spec.role),
            tools=select_tools(spec.tools) if spec.tools else [],
            output_type=_resolve_output_type(spec.output_type),
        )

    # Attach handoffs
    for spec in team.agents:
        parent = agents_by_name[spec.name]
        parent.handoffs = [handoff(agents_by_name[h]) for h in spec.handoffs]

    return agents_by_name[team.entry]


def load_and_build(path_or_name: str) -> Agent:
    """`path_or_name` can be a filename (relative to config/swarm) or a full path."""
    p = Path(path_or_name)
    if not p.exists():
        p = _CONFIG_DIR / path_or_name
        if p.suffix == "":
            p = p.with_suffix(".yaml")
    return build_team(load_team(p))


def list_teams() -> list[str]:
    return sorted(p.stem for p in _CONFIG_DIR.glob("*.yaml"))
