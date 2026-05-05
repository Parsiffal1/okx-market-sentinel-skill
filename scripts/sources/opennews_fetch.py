#!/usr/bin/env python3
"""Fetch the global OpenNews stream for the Phase3 crypto-news layer."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError, HTTPError

from _common import get_env, result_error, result_ok, write_raw_cache

SOURCE = "opennews"
BASE_URL = "https://ai.6551.io"
DEFAULT_SEARCH_PAYLOAD = {"limit": 20, "page": 1}


def fetch_json(url: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> dict:
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def classify_market_bias(items: list[dict]) -> str:
    bullish = 0
    bearish = 0
    for item in items:
        signal = str(item.get("aiRating", {}).get("signal", "neutral")).lower()
        if signal in ("long", "bullish"):
            bullish += 1
        elif signal in ("short", "bearish"):
            bearish += 1
    if bullish >= bearish + 2:
        return "slightly_bullish"
    if bearish >= bullish + 2:
        return "slightly_bearish"
    if bullish and bearish:
        return "mixed"
    return "neutral"


def classify_news_risk(items: list[dict]) -> str:
    high_count = 0
    for item in items:
        score = item.get("aiRating", {}).get("score")
        try:
            score = float(score)
        except Exception:
            continue
        if score >= 80:
            high_count += 1
    if high_count >= 5:
        return "high"
    if high_count >= 2:
        return "medium"
    return "low"


def build_result_summary(items: list[dict], high_impact_events: list[dict], market_bias: str) -> dict:
    return {
        "raw_items": len(items),
        "high_impact_events": len(high_impact_events),
        "market_bias": market_bias,
    }


def build_search_payload() -> dict:
    return dict(DEFAULT_SEARCH_PAYLOAD)


def unique_items_by_id(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    results: list[dict] = []
    for item in items:
        identifier = str(item.get('id') or item.get('newsId') or item.get('text') or '').strip()
        if not identifier or identifier in seen:
            continue
        seen.add(identifier)
        results.append(item)
    return results


def fetch_search_results(token: str) -> tuple[list[dict], list[dict]]:
    payload = build_search_payload()
    result = fetch_json(f"{BASE_URL}/open/news_search", method="POST", payload=payload, token=token)
    items = []
    if isinstance(result, dict) and isinstance(result.get('data'), list):
        items = [item for item in result.get('data', []) if isinstance(item, dict)]
    return unique_items_by_id(items)[:10], [{'payload': payload, 'result': result}]


def main() -> None:
    token = get_env("OPENNEWS_TOKEN")
    if not token:
        path = write_raw_cache("opennews_cache.json", SOURCE, "error", {}, error="OPENNEWS_TOKEN missing")
        result_error(SOURCE, f"OPENNEWS_TOKEN missing, cache written to {path}")
        return

    try:
        items, searches = fetch_search_results(token)
        news_type = fetch_json(f"{BASE_URL}/open/news_type", token=token)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        path = write_raw_cache("opennews_cache.json", SOURCE, "error", {}, error=str(exc))
        result_error(SOURCE, f"failed to fetch opennews, cache written to {path}: {exc}")
        return

    high_impact_events = []
    for item in items:
        score = item.get("aiRating", {}).get("score")
        try:
            score_num = float(score)
        except Exception:
            score_num = 0
        if score_num >= 80:
            high_impact_events.append({
                "title": item.get("text", "")[:180],
                "impact": item.get("aiRating", {}).get("signal", "neutral"),
                "source": item.get("newsType", SOURCE),
                "score": score_num,
            })

    data = {
        "market_bias": classify_market_bias(items),
        "news_risk": classify_news_risk(items),
        "high_impact_events": high_impact_events[:10],
        "source_categories": [x.get("code") for x in news_type.get("data", [])[:10]],
        "raw": {
            "searches": searches,
            "news_type": news_type,
        },
    }

    path = write_raw_cache("opennews_cache.json", SOURCE, "ok", data)
    result_ok(path, SOURCE, build_result_summary(items, high_impact_events, data["market_bias"]))


if __name__ == "__main__":
    main()

