"""Rich-driven terminal REPL."""

from __future__ import annotations

import asyncio
import sys

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent.orchestrator import run_turn
from .swarm.dispatcher import list_teams
from .tools.registry import all_tool_names

load_dotenv()
app = typer.Typer(help="INDIE_MARKET_ANALYST — terminal REPL.")
console = Console()


@app.command()
def chat(team: str | None = typer.Option(None, help="Force a swarm team.")) -> None:
    """Start an interactive chat loop."""
    console.print(Panel.fit(
        "[bold]INDIE_MARKET_ANALYST[/bold]  — Ctrl-D to quit.\n"
        f"teams: {', '.join(list_teams()) or '(none)'}  |  "
        f"tools: {len(all_tool_names())}",
        border_style="cyan",
    ))
    session_id: str | None = None
    while True:
        try:
            msg = console.input("[bold green]you >[/bold green] ").strip()
        except EOFError:
            console.print("\nbye.")
            return
        if not msg:
            continue
        asyncio.run(_run(msg, session_id, team))


async def _run(msg: str, session_id: str | None, team: str | None) -> None:
    buffer = ""
    final_session = session_id
    async for ev in run_turn(msg, session_id=session_id, team_override=team):
        if ev.kind == "delta":
            console.print(ev.data, end="")
            buffer += ev.data
        elif ev.kind == "tool_call":
            console.print(f"\n[dim]↳ tool: {ev.data}[/dim]")
        elif ev.kind == "handoff":
            console.print(f"\n[dim]→ agent: {ev.data}[/dim]")
            if isinstance(ev.data, dict) and ev.data.get("session_id"):
                final_session = ev.data["session_id"]
        elif ev.kind == "final":
            console.print()
            console.print(Markdown(ev.data.get("markdown", "")))
        elif ev.kind == "error":
            console.print(f"\n[red]error:[/red] {ev.data}")
    if final_session:
        console.print(f"[dim]session={final_session}[/dim]")


@app.command("tools")
def list_tools_cmd() -> None:
    """List discovered tools."""
    for name in all_tool_names():
        console.print(f"- {name}")


@app.command("teams")
def list_teams_cmd() -> None:
    """List configured swarm teams."""
    for name in list_teams():
        console.print(f"- {name}")


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(app())
