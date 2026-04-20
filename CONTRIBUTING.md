# Contributing to indie-market-analyst

Thanks for considering a contribution. This project is a tool-first, swarm-orchestrated Indian-market analyst. It is small, opinionated, and designed so that adding a new tool, skill, or team is a drop-in operation — no registration step, no ceremony.

## Ground rules

- Python 3.12+, managed with `uv`.
- Free-tier data sources and models only in defaults. Paid providers may be supported as opt-in.
- Every Pydantic schema between agents uses `ConfigDict(extra="forbid")`. Don't loosen it.
- Tools must return Pydantic models carrying `source` + `as_of` where applicable.
- No `Co-Authored-By: Claude` in commits or PR descriptions.
- Research-only; never ship trading-advice copy anywhere user-facing.

## Local setup

```bash
uv sync                                   # install deps
cp .env.example .env                      # add your OPENROUTER_API_KEY
uv run pytest                             # run tests
uv run ruff check .                       # lint
uv run uvicorn indie_market_analyst.api_server:app --reload
```

Frontend:

```bash
cd frontend && npm install && npm run dev
```

## Adding a tool

1. Create `indie_market_analyst/tools/<category>/<name>.py`.
2. Decorate the callable with `@function_tool` from the `agents` SDK.
3. Return a Pydantic model (strict; `extra="forbid"`).
4. Export `TOOLS: list[Tool]` at module level. The reflection registry picks it up automatically.

## Adding a skill

Skills live under `indie_market_analyst/skills/<name>/` and contain:
- `SKILL.md` — prompt fragment appended to an agent's instructions.
- `meta.yaml` — triggers, optional tool allowlist, optional `output_type`.

Reference the skill by name from any swarm YAML under `skills: [<name>]`.

## Adding a team

Drop a new YAML under `config/swarm/`. Declare agents, `role`, `tools`, `skills`, `handoffs`, and `output_type`. No code change needed — the dispatcher walks the spec.

## Testing

- Unit tests live under `tests/`. Keep them fast and deterministic.
- The backtest engine is pure pandas/numpy — test it without the LLM loop.
- Orchestrator normalization has dedicated fake-event tests in `tests/test_orchestrator_normalize.py`.

## Pull requests

- Describe the change and motivation.
- Include screenshots for UI-affecting changes.
- CI runs `ruff check`, `pytest`, and the frontend build. Keep them green.

## Security

Do not open public issues for security reports. See `SECURITY.md`.
