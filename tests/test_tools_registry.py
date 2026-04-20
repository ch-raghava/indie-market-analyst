from indie_market_analyst.tools.registry import all_tool_names, by_name, discover


def test_discovers_tools():
    names = all_tool_names()
    assert "get_quote" in names
    assert "render_pdf_report" in names
    assert "render_price_chart" in names
    assert "rsi" in names


def test_unique_names():
    tools = discover()
    assert len(tools) == len(set(tools.keys()))


def test_by_name_raises_on_unknown():
    try:
        by_name("does_not_exist")
    except KeyError:
        return
    raise AssertionError("expected KeyError")
