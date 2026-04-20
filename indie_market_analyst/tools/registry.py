"""Dynamic tool discovery.

Every module under ``indie_market_analyst.tools.*`` that defines a module-level
``TOOLS: list[Tool]`` gets auto-registered. Swarm YAML can then reference tools
by name (``tool.name``) without hard-coded imports.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Iterable
from functools import lru_cache

from agents import Tool

import indie_market_analyst.tools as _tools_pkg


@lru_cache(maxsize=1)
def discover() -> dict[str, Tool]:
    found: dict[str, Tool] = {}
    for mod_info in pkgutil.walk_packages(_tools_pkg.__path__, prefix=_tools_pkg.__name__ + "."):
        if mod_info.ispkg:
            continue
        if mod_info.name.endswith(".registry"):
            continue
        mod = importlib.import_module(mod_info.name)
        tools = getattr(mod, "TOOLS", None)
        if not tools:
            continue
        for t in tools:
            found[t.name] = t
    return found


def by_name(name: str) -> Tool:
    tools = discover()
    if name not in tools:
        raise KeyError(f"unknown tool: {name}. Available: {sorted(tools)}")
    return tools[name]


def select(names: Iterable[str]) -> list[Tool]:
    return [by_name(n) for n in names]


def all_tool_names() -> list[str]:
    return sorted(discover().keys())
