#!/usr/bin/env python3
"""Fetch OKX news for Phase3.

This is the only holdings-aware news source in Phase3. When OKX positions are
present, the fetcher prioritizes those symbols; otherwise it falls back to the
default global news stream.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from _common import result_error, result_ok, write_raw_cache
from okx_positions_fetch import RAW_FILENAME as HOLDINGS_RAW_FILENAME, get_holdings_payload
from semantic_compass import load_semantic_compass

SOURCE = "okx_news"
BASE_DIR = Path(__file__).resolve().parents[2]
HOLDINGS_RAW_PATH = BASE_DIR / 'context' / 'raw' / HOLDINGS_RAW_FILENAME


def run_okx_json(args: list[str]):
    cmd = ["okx", "--profile", "live", *args, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"command failed: {' '.join(cmd)}")
    return json.loads(proc.stdout)


def extract_items(payload):
    if isinstance(payload, dict):
        return payload.get("details") or payload.get("data") or []
    if isinstance(payload, list):
        if payload and isinstance(payload[0], dict):
            return payload[0].get("details", payload)
        return payload
    return []


def classify_market_bias(sentiment_rank_payload, important_payload) -> str:
    items = extract_items(sentiment_rank_payload)
    if items:
        bullish = 0
        bearish = 0
        for item in items[:10]:
            label = str((item.get("sentiment") or {}).get("label", item.get("label", ""))).lower()
            if "bull" in label:
                bullish += 1
            elif "bear" in label:
                bearish += 1
        if bullish >= bearish + 2:
            return "slightly_bullish"
        if bearish >= bullish + 2:
            return "slightly_bearish"
    high_items = extract_items(important_payload)
    if len(high_items) >= 5:
        return "mixed"
    return "neutral"


def load_news_risk_terms() -> dict[str, list[str]]:
    defaults = {
        'severe': [
            'exploit', 'hack', 'drain', 'drains funds', 'breach', 'attacker',
            '被盗', '黑客', '漏洞', '攻击', '冻结', '起诉', 'delist', 'depeg', 'outage',
        ],
        'benign_bullish': [
            'etf inflow', 'etf inflows', 'inflow', 'treasury', 'accumulation', 'buy', 'buys',
            'airdrop', 'applications', 'institutional demand', 'reserve strategy',
        ],
        'isolated_project': [
            'ponzi', 'rug pull', '资金盘', '冷门项目', '小市值项目', 'meme token',
        ],
        'systemic': [
            'stablecoin', 'exchange outage', 'regulatory crackdown', 'liquidity crisis',
            'systemic risk', '监管打击', '流动性危机',
        ],
    }
    compass = load_semantic_compass()
    news_terms = compass.get('news_risk', {}) or {}
    merged: dict[str, list[str]] = {}
    for key, values in defaults.items():
        combined: list[str] = []
        for item in [*values, *(news_terms.get(key) or [])]:
            phrase = str(item or '').strip().lower()
            if phrase and phrase not in combined:
                combined.append(phrase)
        merged[key] = combined
    return merged


def classify_news_risk(important_payload) -> str:
    items = extract_items(important_payload)
    if not items:
        return "low"

    terms = load_news_risk_terms()
    severe_keywords = tuple(terms['severe'])
    benign_bullish_keywords = tuple(terms['benign_bullish'])
    isolated_project_keywords = tuple(terms['isolated_project'])
    systemic_keywords = tuple(terms['systemic'])

    total_score = 0.0
    for item in items:
        title = str(item.get('title') or '').lower()
        sentiment = str((item.get('ccySentiments') or [{}])[0].get('sentiment', '')).lower() if item.get('ccySentiments') else ''
        score = 0.0
        if any(keyword in title for keyword in severe_keywords):
            score += 6
        if any(keyword in title for keyword in systemic_keywords):
            score += 3
        if 'bear' in sentiment:
            score += 1.5
        if any(keyword in title for keyword in benign_bullish_keywords):
            score -= 1.5
        if any(keyword in title for keyword in isolated_project_keywords):
            score -= 1.0
        if 'bull' in sentiment:
            score -= 0.5
        total_score += max(0.0, score)
        if score >= 6:
            return 'high'

    if total_score >= 6:
        return 'high'
    if total_score >= 2.5:
        return 'medium'
    return 'low'


def infer_event_importance(item: dict) -> str:
    risk = classify_news_risk({'details': [item]})
    if risk == 'high':
        return 'high'
    if risk == 'medium':
        return 'medium'
    return 'low'


def build_high_impact_events(items: list[dict]) -> list[dict]:
    return [
        {
            'title': item.get('title', ''),
            'impact': infer_event_importance(item),
            'source': ','.join(item.get('platformList', [])) if item.get('platformList') else SOURCE,
            'id': item.get('id'),
        }
        for item in items[:10]
    ]


def load_holdings_symbols() -> list[str]:
    if HOLDINGS_RAW_PATH.exists():
        try:
            payload = json.loads(HOLDINGS_RAW_PATH.read_text(encoding='utf-8'))
            data = payload.get('data', {}) if isinstance(payload, dict) else {}
            symbols = data.get('prioritized_symbols', [])
            if isinstance(symbols, list):
                return [str(symbol).upper() for symbol in symbols if str(symbol).strip()]
        except Exception:
            pass
    data = get_holdings_payload()
    return [str(symbol).upper() for symbol in data.get('prioritized_symbols', []) if str(symbol).strip()]


def build_news_fetch_actions(holdings_symbols: list[str]) -> dict[str, list[str]]:
    joined = ','.join(holdings_symbols)
    if joined:
        return {
            'latest': ['news', 'latest', '--coins', joined, '--limit', '20'],
            'important': ['news', 'by-coin', '--coins', joined, '--importance', 'high', '--limit', '20'],
            'sentiment_rank': ['news', 'sentiment-rank', '--limit', '10'],
        }
    return {
        'latest': ['news', 'latest', '--limit', '20'],
        'important': ['news', 'important', '--limit', '20'],
        'sentiment_rank': ['news', 'sentiment-rank', '--limit', '10'],
    }


def main() -> None:
    holdings_symbols = load_holdings_symbols()
    actions = build_news_fetch_actions(holdings_symbols)
    try:
        latest = run_okx_json(actions['latest'])
        important = run_okx_json(actions['important'])
        sentiment_rank = run_okx_json(actions['sentiment_rank'])
    except Exception as exc:
        path = write_raw_cache("okx_news_cache.json", SOURCE, "error", {}, error=str(exc))
        result_error(SOURCE, f"failed to fetch OKX news, cache written to {path}: {exc}")
        return

    important_items = extract_items(important)[:10]
    high_impact_events = build_high_impact_events(important_items)

    data = {
        "holdings_mode": bool(holdings_symbols),
        "prioritized_symbols": holdings_symbols,
        "market_bias": classify_market_bias(sentiment_rank, important),
        "news_risk": classify_news_risk(important),
        "high_impact_events": high_impact_events,
        "latest_headlines": [item.get("title", "") for item in extract_items(latest)[:10]],
        "raw": {
            "latest": latest,
            "important": important,
            "sentiment_rank": sentiment_rank,
        },
    }

    path = write_raw_cache("okx_news_cache.json", SOURCE, "ok", data)
    result_ok(path, SOURCE, {"events": len(high_impact_events), "market_bias": data["market_bias"], "holdings_mode": data['holdings_mode'], "prioritized_symbols": holdings_symbols})


if __name__ == "__main__":
    main()
