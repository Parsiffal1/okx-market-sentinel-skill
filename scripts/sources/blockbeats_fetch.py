#!/usr/bin/env python3
"""Fetch BlockBeats macro, market-context, and crypto-native risk inputs."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError, HTTPError

from _common import get_env, result_error, result_ok, write_raw_cache

SOURCE = "blockbeats"
BASE_URL = "http://api-pro.theblockbeats.info"
HERMES_CONFIG = "/root/.hermes/config.yaml"


def fetch_json(path: str, params: dict[str, str] | None = None, api_key: str = "") -> dict:
    url = BASE_URL + path
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers={"api-key": api_key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("status") != 0:
        raise RuntimeError(payload.get("message") or "BlockBeats API error")
    return payload.get("data", {})


def _as_list(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["list", "items", "data", "rows"]:
            if isinstance(data.get(key), list):
                return data.get(key)
    return []


def _first_num(item: dict, keys: list[str]) -> float | None:
    for key in keys:
        if key in item:
            try:
                return float(item[key])
            except Exception:
                continue
    return None


def classify_dxy(items: list[dict]) -> str:
    if len(items) < 2:
        return "unknown"
    first = _first_num(items[0], ["close", "value"])
    last = _first_num(items[-1], ["close", "value"])
    if first is None or last in (None, 0):
        return "unknown"
    delta_pct = ((first - last) / last) * 100
    if delta_pct >= 0.5:
        return "strong"
    if delta_pct <= -0.5:
        return "weak"
    return "neutral"


def classify_us10y(items: list[dict]) -> str:
    if not items:
        return "unknown"
    current = _first_num(items[0], ["close", "value"])
    if current is None:
        return "unknown"
    if current >= 4.5:
        return "high"
    if current >= 4.0:
        return "medium"
    return "low"


def classify_m2(items: list[dict]) -> str:
    if len(items) < 2:
        return "unknown"
    first = _first_num(items[0], ["value", "close"])
    last = _first_num(items[-1], ["value", "close"])
    if first is None or last is None:
        return "unknown"
    if first > last * 1.01:
        return "expanding"
    if first < last * 0.99:
        return "contracting"
    return "flat"


def classify_flow(items: list[dict], keys: list[str]) -> str:
    if not items:
        return "unknown"
    current = _first_num(items[0], keys)
    if current is None:
        return "unknown"
    if current > 0:
        return "positive"
    if current < 0:
        return "negative"
    return "neutral"


def main() -> None:
    api_key = get_env("BLOCKBEATS_API_KEY")
    if not api_key:
        try:
            import yaml
            with open(HERMES_CONFIG, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            api_key = (((cfg.get("mcp_servers", {}) or {}).get("blockbeats", {}) or {}).get("env", {}) or {}).get("BLOCKBEATS_API_KEY", "")
        except Exception:
            api_key = ""
    if not api_key:
        path = write_raw_cache("blockbeats_cache.json", SOURCE, "error", {}, error="BLOCKBEATS_API_KEY missing")
        result_error(SOURCE, f"BLOCKBEATS_API_KEY missing, cache written to {path}")
        return

    endpoints = {
        "newsflash": ("/v1/newsflash/important", {"page": "1", "size": "20", "lang": "cn"}),
        "dxy": ("/v1/data/dxy", {"type": "1W"}),
        "us10y": ("/v1/data/us10y", {"type": "1W"}),
        "m2": ("/v1/data/m2_supply", {"type": "6M"}),
        "btc_etf": ("/v1/data/btc_etf", None),
        "stablecoin": ("/v1/data/stablecoin_marketcap", None),
        "onchain_tx": ("/v1/data/daily_tx", None),
        "contract_oi": ("/v1/data/contract", {"dataType": "1W"}),
        "sentiment": ("/v1/data/bottom_top_indicator", None),
    }

    raw: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for name, (path, params) in endpoints.items():
        try:
            raw[name] = fetch_json(path, params, api_key)
        except Exception as exc:
            errors[name] = str(exc)

    if len(errors) == len(endpoints):
        path = write_raw_cache("blockbeats_cache.json", SOURCE, "error", {"errors": errors}, error="all endpoints failed")
        result_error(SOURCE, f"all endpoints failed, cache written to {path}")
        return

    news_items = _as_list(raw.get("newsflash", {}))
    dxy_items = _as_list(raw.get("dxy", {}))
    us10y_items = _as_list(raw.get("us10y", {}))
    m2_items = _as_list(raw.get("m2", {}))
    btc_etf_items = _as_list(raw.get("btc_etf", {}))
    stablecoin_map = raw.get("stablecoin", {}) if isinstance(raw.get("stablecoin", {}), dict) else {}
    onchain_networks = raw.get("onchain_tx", []) if isinstance(raw.get("onchain_tx", []), list) else []
    contract_items = _as_list(raw.get("contract_oi", {}))
    sentiment_items = _as_list(raw.get("sentiment", {}))

    def stablecoin_state() -> str:
        try:
            latest = 0.0
            prev = 0.0
            for key in ["usdt", "usdc"]:
                arr = stablecoin_map.get(key, [])
                if len(arr) >= 2:
                    latest += float(arr[0].get("market_cap", 0))
                    prev += float(arr[1].get("market_cap", 0))
            if latest > prev * 1.002:
                return "expanding"
            if latest < prev * 0.998:
                return "contracting"
            return "flat"
        except Exception:
            return "unknown"

    def onchain_state() -> str:
        try:
            growth = 0
            checked = 0
            for chain in onchain_networks[:5]:
                arr = chain.get("data", [])
                if len(arr) >= 2:
                    latest = float(arr[-1].get("daily_transactions", 0))
                    prev = float(arr[-2].get("daily_transactions", 0))
                    checked += 1
                    if latest > prev:
                        growth += 1
            if checked == 0:
                return "unknown"
            if growth >= checked * 0.6:
                return "positive"
            if growth <= checked * 0.4:
                return "negative"
            return "neutral"
        except Exception:
            return "unknown"

    def sentiment_state() -> str:
        statuses = [str(x.get("status", "")).lower() for x in sentiment_items[:5]]
        if any("buy" in s for s in statuses):
            return "positive"
        if any("sell" in s for s in statuses):
            return "negative"
        if any("hold" in s for s in statuses):
            return "neutral"
        return "unknown"

    high_impact_events = [
        {
            "title": item.get("title") or item.get("summary_zh") or "",
            "impact": item.get("signal", "neutral"),
            "source": item.get("source", SOURCE),
            "score": item.get("score"),
        }
        for item in news_items[:10]
    ]

    data = {
        "macro": {
            "usd_strength": classify_dxy(dxy_items),
            "us10y_pressure": classify_us10y(us10y_items),
            "m2_trend": classify_m2(m2_items),
            "macro_summary": [item.get("summary_zh") or item.get("title", "") for item in news_items[:3]],
        },
        "crypto_news": {
            "market_bias": "neutral",
            "high_impact_events": high_impact_events,
        },
        "market_context": {
            "btc_etf_flow": classify_flow(btc_etf_items, ["day_net_inflow_million", "netInflow", "value", "close"]),
            "stablecoin_liquidity": stablecoin_state(),
            "onchain_tx_trend": onchain_state(),
            "contract_oi_environment": classify_flow(contract_items, ["binance_open_interest", "bybit_open_interest", "hyperliquid_open_interest", "value", "close", "oi"]),
            "sentiment_indicator": sentiment_state(),
        },
        "raw": raw,
        "errors": errors,
    }

    status = "ok" if not errors else "partial"
    cache_path = write_raw_cache("blockbeats_cache.json", SOURCE, status, data, error=json.dumps(errors, ensure_ascii=False) if errors else None)
    result_ok(cache_path, SOURCE, {"status": status, "errors": errors, "events": len(high_impact_events)})


if __name__ == "__main__":
    main()
