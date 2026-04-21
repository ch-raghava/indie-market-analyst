"""Stealth-config tests for the Playwright news scraper.

No live HTTP. The ``_browser()`` test monkeypatches
``playwright.sync_api.sync_playwright`` with a mock chain so we can
assert on the kwargs passed to ``new_context`` and the init script
registered before the first page is created.

Covers the four hardening fixes from toslove.txt Phase 2b:
  1. init_script masks navigator.webdriver / languages / plugins / chrome.
  2. sec-ch-ua + Sec-Fetch-* + Accept-Language headers match the pinned UA.
  3. Pinned UA Chrome version matches the sec-ch-ua brand version.
  4. URL-regex link discovery picks only article URLs out of a mixed page.
"""
from __future__ import annotations

import re
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from indie_market_analyst.tools.market_data import playwright_scraper as ps

# ---------------------------------------------------------------------------
# Test 1: context receives stealth headers + init_script
# ---------------------------------------------------------------------------

def test_context_receives_stealth_headers_and_init_script(monkeypatch):
    context = MagicMock(name="context")
    browser = MagicMock(name="browser")
    browser.new_context.return_value = context
    pw_chain = MagicMock(name="pw")
    pw_chain.chromium.launch.return_value = browser

    # sync_playwright() returns an object whose .start() gives the chain.
    sp_factory = MagicMock(name="sync_playwright")
    sp_factory.return_value.start.return_value = pw_chain

    # Inject a fake playwright.sync_api module exposing sync_playwright.
    fake_mod = ModuleType("playwright.sync_api")
    fake_mod.sync_playwright = sp_factory  # type: ignore[attr-defined]
    fake_pkg = ModuleType("playwright")
    fake_pkg.sync_api = fake_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", fake_pkg)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake_mod)

    with ps._browser() as ctx:
        assert ctx.page is context.new_page.return_value

    # UA pinned.
    _, kwargs = browser.new_context.call_args
    assert kwargs["user_agent"] == ps._UA

    # Stealth headers present and correct.
    headers = kwargs["extra_http_headers"]
    assert headers["sec-ch-ua"] == ps._SEC_CH_UA
    assert headers["sec-ch-ua-mobile"] == "?0"
    assert headers["sec-ch-ua-platform"] == '"Linux"'
    assert headers["Upgrade-Insecure-Requests"] == "1"
    assert headers["Accept-Language"] == "en-IN,en;q=0.9"
    for h in ("Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-User", "Sec-Fetch-Dest"):
        assert h in headers

    # init_script registered exactly once, before new_page.
    context.add_init_script.assert_called_once()
    script = context.add_init_script.call_args.args[0]
    for needle in ("webdriver", "languages", "plugins", "window.chrome"):
        assert needle in script, f"init_script missing {needle!r}"

    # Ordering: add_init_script must fire before the first new_page call.
    method_names = [name for name, _args, _kwargs in context.method_calls]
    assert method_names.index("add_init_script") < method_names.index("new_page"), (
        f"add_init_script must precede new_page; got order {method_names}"
    )


# ---------------------------------------------------------------------------
# Test 2: URL-regex link discovery per site
# ---------------------------------------------------------------------------

_SITE_FIXTURES = {
    "moneycontrol": {
        "html": """
            <a href="/news/business/markets/sensex-nifty-close-lower-today-12345.html">A</a>
            <a href="https://www.moneycontrol.com/news/business/markets/rbi-rate-decision-99999.html">B</a>
            <a href="/">home</a>
            <a href="/news/business/markets/">index</a>
            <a href="https://twitter.com/share">share</a>
        """,
        "expected": {
            "https://www.moneycontrol.com/news/business/markets/sensex-nifty-close-lower-today-12345.html",
            "https://www.moneycontrol.com/news/business/markets/rbi-rate-decision-99999.html",
        },
    },
    "livemint": {
        "html": """
            <a href="https://www.livemint.com/market/stock-market-news/nifty-today-11712345678901.html">A</a>
            <a href="https://www.livemint.com/companies/news/tcs-results-11798765432101.html">B</a>
            <a href="/">home</a>
            <a href="/market">section</a>
            <a href="https://www.livemint.com/opinion/columns">opinion-index</a>
        """,
        "expected": {
            "https://www.livemint.com/market/stock-market-news/nifty-today-11712345678901.html",
            "https://www.livemint.com/companies/news/tcs-results-11798765432101.html",
        },
    },
    "economictimes": {
        "html": """
            <a href="/markets/stocks/news/nifty-hits-record/articleshow/98765432.cms">A</a>
            <a href="https://economictimes.indiatimes.com/markets/commodities/articleshow/11111111.cms">B</a>
            <a href="/markets">section</a>
            <a href="/">home</a>
            <a href="https://twitter.com/intent">share</a>
        """,
        "expected": {
            "https://economictimes.indiatimes.com/markets/stocks/news/nifty-hits-record/articleshow/98765432.cms",
            "https://economictimes.indiatimes.com/markets/commodities/articleshow/11111111.cms",
        },
    },
    "businessstandard": {
        "html": """
            <a href="/markets/news/sensex-live-today-124123456_1.html">A</a>
            <a href="https://www.business-standard.com/companies/results/hdfc-q4-987654321.html">B</a>
            <a href="/markets">section</a>
            <a href="/">home</a>
            <a href="https://facebook.com/share">share</a>
        """,
        "expected": {
            "https://www.business-standard.com/markets/news/sensex-live-today-124123456_1.html",
            "https://www.business-standard.com/companies/results/hdfc-q4-987654321.html",
        },
    },
    "ndtvprofit": {
        "html": """
            <a href="/markets/nestle-shares-jump-over-4-after-q4-results-11387236">A</a>
            <a href="https://www.ndtvprofit.com/business/hcltech-declares-dividend-11387459">B</a>
            <a href="/markets/stocks">section</a>
            <a href="/markets/commodities">section2</a>
            <a href="/">home</a>
            <a href="https://twitter.com/share">share</a>
        """,
        "expected": {
            "https://www.ndtvprofit.com/markets/nestle-shares-jump-over-4-after-q4-results-11387236",
            "https://www.ndtvprofit.com/business/hcltech-declares-dividend-11387459",
        },
    },
}


@pytest.mark.parametrize("site_key", list(_SITE_FIXTURES.keys()))
def test_link_pattern_extraction(site_key):
    spec = ps.SITES[site_key]
    fixture = _SITE_FIXTURES[site_key]

    raw_hrefs = re.findall(r'href=["\']([^"\']+)["\']', fixture["html"])
    matched = {
        abs_url
        for href in raw_hrefs
        for abs_url in [ps._absolutize(href.strip(), spec.link_prefix)]
        if abs_url and spec.link_pattern.search(abs_url)
    }
    assert matched == fixture["expected"], (
        f"{site_key} regex {spec.link_pattern.pattern!r} "
        f"matched {matched}, expected {fixture['expected']}"
    )


# ---------------------------------------------------------------------------
# Test 3: UA / sec-ch-ua brand version consistency
# ---------------------------------------------------------------------------

def test_pinned_ua_matches_sec_ch_ua_brand():
    ua_match = re.search(r"Chrome/(\d+)", ps._UA)
    hint_match = re.search(r'"Google Chrome";v="(\d+)"', ps._SEC_CH_UA)
    assert ua_match, f"_UA has no Chrome version: {ps._UA!r}"
    assert hint_match, f"_SEC_CH_UA has no Google Chrome brand: {ps._SEC_CH_UA!r}"
    assert ua_match.group(1) == hint_match.group(1), (
        f"UA Chrome v{ua_match.group(1)} != sec-ch-ua Google Chrome v{hint_match.group(1)}"
    )
