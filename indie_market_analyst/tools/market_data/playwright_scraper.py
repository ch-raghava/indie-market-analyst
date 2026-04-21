"""Headless-browser news scraper for Indian financial sites.

Complements the RSS-based ``news_tool``:
  - Full-article body extraction (richer summaries, deeper sentiment).
  - Sites without usable RSS (or where RSS is stale).
  - Fallback path when RSS returns nothing.

Design goals:
  - **Robust.** Per-domain rate limit, UA rotation, retries with backoff,
    navigation/total timeouts, graceful degradation (skip failures).
  - **Cheap.** Blocks images/fonts/media at request level; caches responses
    in SQLite via ``MemoryStore`` (TTL-gated).
  - **Deterministic.** Sentiment is reused from ``news_tool._label`` — the
    LLM never sees numbers it can't justify.
  - **Simple.** Sync Playwright; same shape as other ``@function_tool``s.

Install:
  ``uv sync`` pulls Playwright the package; browser binaries come from
  ``uv run playwright install chromium`` (one-time, ~170 MB).
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agents import function_tool
from pydantic import BaseModel, ConfigDict, Field

from indie_market_analyst.memory.store import get_store
from indie_market_analyst.tools.market_data.news_tool import (
    NewsItem,
    _dedupe,
    _label,
    _sort_recent,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_UAS: tuple[str, ...] = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
)

_BLOCK_RESOURCES = {"image", "media", "font", "stylesheet"}
_NAV_TIMEOUT_MS = 15_000
_TOTAL_TIMEOUT_S = 30.0
_PER_DOMAIN_GAP_S = 2.0
_CACHE_TTL_S = 900  # 15 min
_MAX_RETRIES = 3
_BACKOFF_BASE_S = 1.5

_CACHE_TAG_PREFIX = "scrape_cache:"


@dataclass
class SiteSpec:
    """Per-site scraping contract.

    ``list_url`` is where we look for fresh links.
    ``link_selector`` yields ``<a href>`` elements on the list page.
    ``body_selectors`` are tried in order on each article page — the first
    non-empty wins. A final generic fallback (``article``, ``[itemprop=articleBody]``)
    is always tried so a broken site-specific selector degrades, not crashes.
    """

    key: str
    label: str
    list_url: str
    link_selector: str
    body_selectors: tuple[str, ...]
    link_prefix: str = ""


SITES: dict[str, SiteSpec] = {
    "moneycontrol": SiteSpec(
        key="moneycontrol",
        label="Moneycontrol",
        list_url="https://www.moneycontrol.com/news/business/markets/",
        link_selector="li.clearfix h2 a, .news_row h2 a",
        body_selectors=(".content_wrapper .arti-flow", "div#contentdata", ".arti-flow"),
    ),
    "livemint": SiteSpec(
        key="livemint",
        label="Livemint",
        list_url="https://www.livemint.com/market",
        link_selector="a.imgSec, h2.headline a, h3 a",
        body_selectors=(
            "div.storyParagraph",
            "[itemprop='articleBody']",
            "div.mainArea",
        ),
    ),
    "economictimes": SiteSpec(
        key="economictimes",
        label="Economic Times",
        list_url="https://economictimes.indiatimes.com/markets",
        link_selector="h3 a, h2 a, .eachStory a",
        body_selectors=(".artText", "[itemprop='articleBody']", ".article_content"),
        link_prefix="https://economictimes.indiatimes.com",
    ),
    "businessstandard": SiteSpec(
        key="businessstandard",
        label="Business Standard",
        list_url="https://www.business-standard.com/markets",
        link_selector="a.smallcard-title, h2 a, h3 a",
        body_selectors=(".storycontent", ".article-content", "[itemprop='articleBody']"),
        link_prefix="https://www.business-standard.com",
    ),
    "ndtvprofit": SiteSpec(
        key="ndtvprofit",
        label="NDTV Profit",
        list_url="https://www.ndtvprofit.com/markets",
        link_selector="h3 a, h2 a, a.story-card-link",
        body_selectors=("[itemprop='articleBody']", "article", ".story-element-text"),
        link_prefix="https://www.ndtvprofit.com",
    ),
}


# ---------------------------------------------------------------------------
# Rate limit (process-wide, per host)
# ---------------------------------------------------------------------------

_domain_gate: dict[str, float] = {}
_domain_lock = threading.Lock()


def _rate_limit(host: str, gap: float = _PER_DOMAIN_GAP_S) -> None:
    with _domain_lock:
        last = _domain_gate.get(host, 0.0)
        wait = gap - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        _domain_gate[host] = time.time()


def _host_of(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else url


# ---------------------------------------------------------------------------
# SQLite cache (via existing MemoryStore.observations)
# ---------------------------------------------------------------------------

def _cache_key(name: str, *parts: str) -> str:
    raw = "::".join([name, *parts])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _cache_get(key: str, ttl: int = _CACHE_TTL_S) -> Any | None:
    store = get_store()
    rows = store.recent_observations(tag=f"{_CACHE_TAG_PREFIX}{key}", limit=1)
    if not rows:
        return None
    row = rows[0]
    if time.time() - (row.get("created_at") or 0) > ttl:
        return None
    try:
        return json.loads(row["text"])
    except (ValueError, KeyError):
        return None


def _cache_set(key: str, value: Any) -> None:
    try:
        payload = json.dumps(value, default=str)
    except (TypeError, ValueError):
        return
    try:
        get_store().add_observation(text=payload, tag=f"{_CACHE_TAG_PREFIX}{key}")
    except Exception as e:  # store errors must never kill a scrape
        log.debug("cache_set failed: %s", e)


# ---------------------------------------------------------------------------
# Playwright lifecycle
# ---------------------------------------------------------------------------

@dataclass
class _BrowserCtx:
    browser: Any
    context: Any
    page: Any
    pw: Any
    errors: list[str] = field(default_factory=list)


@contextmanager
def _browser(user_agent: str | None = None):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "playwright not installed. Run: uv sync && uv run playwright install chromium"
        ) from e

    ua = user_agent or random.choice(_UAS)
    pw = sync_playwright().start()
    browser = None
    try:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            user_agent=ua,
            viewport={"width": 1366, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True,
        )
        context.set_default_navigation_timeout(_NAV_TIMEOUT_MS)
        context.set_default_timeout(_NAV_TIMEOUT_MS)

        def _router(route: Any) -> None:
            if route.request.resource_type in _BLOCK_RESOURCES:
                route.abort()
            else:
                route.continue_()

        context.route("**/*", _router)
        page = context.new_page()
        yield _BrowserCtx(browser=browser, context=context, page=page, pw=pw)
    finally:
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Retries
# ---------------------------------------------------------------------------

def _with_retry(fn, *, label: str, attempts: int = _MAX_RETRIES):
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 — scraper must be fault-tolerant
            last_err = e
            backoff = _BACKOFF_BASE_S * (2**i) + random.uniform(0, 0.5)
            log.info("scrape retry %d/%d for %s: %s (sleep %.1fs)",
                     i + 1, attempts, label, e, backoff)
            time.sleep(backoff)
    log.warning("scrape gave up on %s: %s", label, last_err)
    return None


# ---------------------------------------------------------------------------
# Core scraping primitives
# ---------------------------------------------------------------------------

def _absolutize(href: str, prefix: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return prefix + href
    return href


def _extract_body(page: Any, selectors: tuple[str, ...]) -> str:
    """Try site-specific selectors first, then generic fallbacks."""
    fallback = ("article", "[itemprop='articleBody']", "main")
    for sel in (*selectors, *fallback):
        try:
            el = page.query_selector(sel)
            if not el:
                continue
            txt = el.inner_text(timeout=3000)
            txt = re.sub(r"\s+\n", "\n", txt).strip()
            if len(txt) > 200:
                return txt
        except Exception:
            continue
    try:
        return (page.inner_text("body", timeout=3000) or "").strip()
    except Exception:
        return ""


def _scrape_list(page: Any, spec: SiteSpec, limit: int) -> list[str]:
    page.goto(spec.list_url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector(spec.link_selector, timeout=6000)
    except Exception:
        pass
    hrefs: list[str] = []
    try:
        elements = page.query_selector_all(spec.link_selector)
    except Exception:
        elements = []
    for el in elements[: limit * 3]:  # oversample; many will be nav/promos
        try:
            href = el.get_attribute("href") or ""
        except Exception:
            continue
        href = _absolutize(href.strip(), spec.link_prefix)
        if not href or "#" in href.split("/")[-1]:
            continue
        if href in hrefs:
            continue
        hrefs.append(href)
        if len(hrefs) >= limit:
            break
    return hrefs


def _scrape_article(page: Any, spec: SiteSpec, url: str) -> NewsItem | None:
    _rate_limit(_host_of(url))
    cache_k = _cache_key("article", url)
    hit = _cache_get(cache_k)
    if hit:
        try:
            return NewsItem(**hit)
        except Exception:
            pass

    page.goto(url, wait_until="domcontentloaded")
    title = ""
    try:
        title = (page.title() or "").strip()
    except Exception:
        pass
    # Prefer og:title when available
    try:
        og = page.query_selector("meta[property='og:title']")
        if og:
            v = og.get_attribute("content") or ""
            if v:
                title = v.strip()
    except Exception:
        pass
    if not title:
        return None

    body = _extract_body(page, spec.body_selectors)
    if not body:
        return None

    pub: str | None = None
    for meta_sel in (
        "meta[property='article:published_time']",
        "meta[name='publishdate']",
        "meta[itemprop='datePublished']",
    ):
        try:
            m = page.query_selector(meta_sel)
            if m:
                v = m.get_attribute("content") or ""
                if v:
                    try:
                        pub = datetime.fromisoformat(
                            v.replace("Z", "+00:00")
                        ).astimezone(UTC).isoformat()
                        break
                    except Exception:
                        pass
        except Exception:
            continue

    summary = re.sub(r"\s+", " ", body)[:600].strip()
    item = NewsItem(
        title=title,
        link=url,
        published_utc=pub,
        summary=summary,
        source=spec.label,
        sentiment=_label(f"{title}. {summary}"),
    )
    _cache_set(cache_k, item.model_dump())
    return item


def scrape_site(
    spec: SiteSpec,
    topic: str | None,
    limit: int,
    ctx: _BrowserCtx,
) -> list[NewsItem]:
    """Scrape one site — list page then each article. Never raises."""
    deadline = time.time() + _TOTAL_TIMEOUT_S
    _rate_limit(_host_of(spec.list_url))

    list_cache_k = _cache_key("list", spec.key)
    hrefs = _cache_get(list_cache_k, ttl=300) or []
    if not hrefs:
        hrefs = _with_retry(
            lambda: _scrape_list(ctx.page, spec, limit),
            label=f"{spec.key}:list",
        ) or []
        if hrefs:
            _cache_set(list_cache_k, hrefs)

    items: list[NewsItem] = []
    for url in hrefs:
        if time.time() > deadline:
            log.info("scrape_site %s hit total timeout", spec.key)
            break
        try:
            item = _with_retry(
                lambda u=url: _scrape_article(ctx.page, spec, u),
                label=f"{spec.key}:article",
                attempts=2,
            )
        except Exception as e:
            ctx.errors.append(f"{spec.key}: {e}")
            continue
        if not item:
            continue
        if topic:
            hay = f"{item.title} {item.summary}".lower()
            if topic.lower() not in hay:
                continue
        items.append(item)
        if len(items) >= limit:
            break
    return items


# ---------------------------------------------------------------------------
# Tool-level entry points
# ---------------------------------------------------------------------------

class DeepNewsDigest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[NewsItem]
    total: int
    bullish: int
    bearish: int
    neutral: int
    overall_sentiment: str = Field(
        description="bullish | bearish | mixed | neutral — aggregate read"
    )
    sentiment_score: float = Field(description="(bull - bear) / total, in [-1,1]")
    as_of_utc: str
    sources_used: list[str]
    sources_failed: list[str] = Field(default_factory=list)


def _aggregate(items: list[NewsItem]) -> tuple[int, int, int, str, float]:
    bulls = sum(1 for i in items if i.sentiment == "bull")
    bears = sum(1 for i in items if i.sentiment == "bear")
    neut = sum(1 for i in items if i.sentiment == "neutral")
    total = len(items)
    score = 0.0 if total == 0 else round((bulls - bears) / total, 3)
    if total == 0:
        mood = "neutral"
    elif score >= 0.25:
        mood = "bullish"
    elif score <= -0.25:
        mood = "bearish"
    elif bulls > 0 and bears > 0:
        mood = "mixed"
    else:
        mood = "neutral"
    return bulls, bears, neut, mood, score


def scrape_deep(
    sites: list[str] | None = None,
    topic: str | None = None,
    limit_per_site: int = 4,
) -> DeepNewsDigest:
    """Scrape all selected sites with one shared browser.

    Public (non-``@function_tool``) entry point so ``news_tool.get_market_news``
    can use it as an RSS fallback.
    """
    picked = [SITES[k] for k in (sites or list(SITES.keys())) if k in SITES]
    sources_used: list[str] = []
    sources_failed: list[str] = []
    collected: list[NewsItem] = []

    with _browser() as ctx:
        for spec in picked:
            try:
                batch = scrape_site(spec, topic, limit_per_site, ctx)
            except Exception as e:
                log.warning("site %s crashed: %s", spec.key, e)
                sources_failed.append(spec.key)
                continue
            if batch:
                sources_used.append(spec.key)
                collected.extend(batch)
            else:
                sources_failed.append(spec.key)

    items = _sort_recent(_dedupe(collected))
    bulls, bears, neut, mood, score = _aggregate(items)
    return DeepNewsDigest(
        items=items,
        total=len(items),
        bullish=bulls,
        bearish=bears,
        neutral=neut,
        overall_sentiment=mood,
        sentiment_score=score,
        as_of_utc=datetime.now(UTC).isoformat(),
        sources_used=sources_used,
        sources_failed=sources_failed,
    )


@function_tool
def get_market_news_deep(
    topic: str = "",
    limit_per_site: int = 4,
    sites: str = "",
) -> DeepNewsDigest:
    """Playwright-rendered deep news with full article bodies + sentiment.

    Slower than :func:`get_market_news` (seconds, not ms) — prefer the RSS tool
    for quick headlines. Use this when the user wants article substance, when a
    specific site is named, or when RSS returns nothing.

    Args:
        topic: keyword filter applied post-scrape to title+body
            (e.g. ``"reliance"``, ``"rbi"``). Empty = no filter.
        limit_per_site: articles to fetch per site (1-8). Total is capped
            at limit_per_site * len(sites).
        sites: comma-separated subset of
            ``moneycontrol,livemint,economictimes,businessstandard,ndtvprofit``.
            Empty = all five.
    """
    limit_per_site = max(1, min(int(limit_per_site), 8))
    topic_q = topic.strip() or None
    selected = [s.strip() for s in sites.split(",") if s.strip()] or None
    if selected:
        selected = [s for s in selected if s in SITES]
    return scrape_deep(sites=selected, topic=topic_q, limit_per_site=limit_per_site)


TOOLS = [get_market_news_deep]


# ---------------------------------------------------------------------------
# Cache eviction helper (optional, for cron/housekeeping)
# ---------------------------------------------------------------------------

def purge_expired_cache(ttl: int = _CACHE_TTL_S) -> int:
    """Best-effort cleanup of expired cache observations. Returns count removed."""
    store = get_store()
    cutoff = time.time() - ttl
    removed = 0
    with store._conn() as c:  # noqa: SLF001 — housekeeping uses the raw conn
        cur = c.execute(
            "DELETE FROM observations WHERE tag LIKE ? AND created_at < ?",
            (f"{_CACHE_TAG_PREFIX}%", cutoff),
        )
        removed = cur.rowcount or 0
    return removed


__all__ = [
    "DeepNewsDigest",
    "SITES",
    "SiteSpec",
    "TOOLS",
    "get_market_news_deep",
    "purge_expired_cache",
    "scrape_deep",
]
