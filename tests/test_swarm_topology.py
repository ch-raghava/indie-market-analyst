from pathlib import Path

from indie_market_analyst.swarm.topology import load_team


def test_eod_pipeline_parses():
    path = Path("config/swarm/eod_report_pipeline.yaml")
    team = load_team(path)
    assert team.team == "eod_report_pipeline"
    m = team.agent_map()  # validates handoffs + entry
    assert team.entry in m
    assert "report_writer" in m
    assert m["report_writer"].handoffs == []


def test_equity_research_parses():
    team = load_team(Path("config/swarm/equity_research.yaml"))
    assert team.entry == "equity_researcher"
