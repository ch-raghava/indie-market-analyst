"""Skill discovery and mounting.

A skill is a directory under ``indie_market_analyst/skills/`` containing:
  * ``SKILL.md`` — the prompt fragment / instructions.
  * ``meta.yaml`` — ``name``, ``triggers`` (keywords), ``tools`` (optional
    tool-name allowlist), ``output_type`` (optional), ``templates/`` (for
    report-style skills).

Skills are mounted ephemerally: when the orchestrator's router sees a trigger
keyword in the user turn, it concatenates the SKILL.md into the target agent's
``instructions`` for just that turn.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_SKILLS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Skill:
    name: str
    dir: Path
    instructions: str
    triggers: tuple[str, ...]
    tools: tuple[str, ...]           # optional tool allowlist
    output_type: str | None          # dotted Pydantic class path, optional


@lru_cache(maxsize=1)
def discover() -> dict[str, Skill]:
    out: dict[str, Skill] = {}
    for sub in _SKILLS_DIR.iterdir():
        if not sub.is_dir() or sub.name.startswith("_"):
            continue
        meta_path = sub / "meta.yaml"
        skill_md = sub / "SKILL.md"
        if not meta_path.exists() or not skill_md.exists():
            continue
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        out[meta.get("name", sub.name)] = Skill(
            name=meta.get("name", sub.name),
            dir=sub,
            instructions=skill_md.read_text(encoding="utf-8"),
            triggers=tuple(meta.get("triggers", []) or []),
            tools=tuple(meta.get("tools", []) or []),
            output_type=meta.get("output_type"),
        )
    return out


def match(text: str) -> list[Skill]:
    t = text.lower()
    return [s for s in discover().values() if any(k.lower() in t for k in s.triggers)]
