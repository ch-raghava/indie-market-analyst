"""YAML topology schema.

Example (``config/swarm/eod_report_pipeline.yaml``):

```yaml
team: eod_report_pipeline
description: Collector -> Verifier -> Calculator -> PDF Writer
entry: orchestrator
agents:
  - name: orchestrator
    role: orchestrator
    instructions: >
      You delegate end-to-end. Never answer directly; always handoff.
    handoffs: [collector]
  - name: collector
    role: collector
    tools: [get_quote, get_history, get_index_snapshot, get_advance_decline]
    handoffs: [verifier]
  ...
```
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ..core.errors import TopologyError


class AgentSpec(BaseModel):
    name: str
    role: str
    instructions: str = ""
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)   # skill names to always mount
    handoffs: list[str] = Field(default_factory=list) # sibling agent names
    output_type: str | None = None                    # dotted Pydantic class path


class TeamSpec(BaseModel):
    team: str
    description: str = ""
    entry: str
    agents: list[AgentSpec]

    def agent_map(self) -> dict[str, AgentSpec]:
        m = {a.name: a for a in self.agents}
        if self.entry not in m:
            raise TopologyError(f"entry agent {self.entry!r} not in team {self.team!r}")
        for a in self.agents:
            for h in a.handoffs:
                if h not in m:
                    raise TopologyError(f"handoff {h!r} from {a.name!r} not found in team")
        return m


def load_team(path: Path | str) -> TeamSpec:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return TeamSpec.model_validate(data)
