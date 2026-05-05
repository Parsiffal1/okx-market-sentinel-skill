#!/usr/bin/env python3
"""Fetch whitelisted X/Twitter accounts and derive Phase3 social signals."""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError

from _common import get_env, result_error, result_ok, write_raw_cache

SOURCE = "opentwitter"
BASE_URL = "https://ai.6551.io"
SOURCES_FILE = Path(__file__).resolve().parents[2] / "config" / "phase3_sources.yaml"
RULES_FILE = Path(__file__).resolve().parents[2] / "config" / "phase3_rules.yaml"
DEFAULT_SOCIAL_RULES = {
    "heat_weights": {
        "view_count": 1,
        "favorite_count": 20,
        "reply_count": 30,
    },
    "major_aliases": {
        "BTC": ["BTC", "btc", "大饼", "比特币", "XBT", "xbt"],
        "ETH": ["ETH", "eth", "二饼", "以太", "姨太", "Ethereum", "ethereum"],
        "SOL": ["SOL", "sol", "Solana", "solana"],
    },
    "symbol_ignore_tokens": [
        "CRYPTO",
        "MEME",
        "FOMO",
        "BLOCKBEATS",
        "COINGLASS",
        "LATEST",
        "BINANCE",
        "BITGET",
        "VIP",
        "ZACHXBT",
        "MSTR",
        "LTH",
        "EMA",
        "HTTPS",
        "APP",
        "COM",
        "LINK",
        "COPYLINK",
        "SOURCE",
        "SHARE",
        "SQUARE",
        "HOST",
        "WEB",
        "UNI",
        "CSPA",
        "OBGWVH",
        "MAYBE",
        "HIGHER",
        "TODAY",
        "YESTERDAY",
        "BREAKING",
        "LOOK",
        "JUST",
        "CONTINUE",
        "CONTINUES",
        "BULLISH",
        "BEARISH",
        "LONG",
        "SHORT",
    ],
    "high_risk_keywords": ["rug", "scam", "exploit", "hacked", "归零"],
}


def fetch_json(url: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sanitize_tweet_item(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "text": item.get("text", ""),
        "createdAt": item.get("createdAt"),
        "viewCount": item.get("viewCount", 0),
        "favoriteCount": item.get("favoriteCount", 0),
        "replyCount": item.get("replyCount", 0),
        "userScreenName": item.get("userScreenName"),
        "userName": item.get("userName"),
        "userIdStr": item.get("userIdStr"),
        "userFollowers": item.get("userFollowers"),
        "media": item.get("media"),
        "urls": item.get("urls"),
    }


def fetch_okx_instruments(inst_type: str) -> list[dict]:
    cmd = ["okx", "--profile", "live", "market", "instruments", "--instType", inst_type, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"okx instruments failed: {inst_type}")
    payload = json.loads(proc.stdout)
    if isinstance(payload, dict) and "data" in payload:
        payload = payload.get("data") or []
    return payload if isinstance(payload, list) else []


def extract_symbol_from_inst_id(inst_id: str) -> str | None:
    if not inst_id:
        return None
    base = str(inst_id).split("-", 1)[0].strip().upper()
    return base or None


def fetch_okx_tradable_symbols() -> set[str]:
    symbols: set[str] = set()
    for inst_type in ["SWAP", "FUTURES"]:
        for item in fetch_okx_instruments(inst_type):
            if str(item.get("state", "")).lower() != "live":
                continue
            symbol = extract_symbol_from_inst_id(str(item.get("instId", "")))
            if symbol:
                symbols.add(symbol)
    return symbols


def filter_symbol_mentions_by_okx_symbols(symbol_mentions: list[dict], okx_symbols: set[str] | None) -> list[dict]:
    if not okx_symbols:
        return symbol_mentions
    filtered = []
    for item in symbol_mentions:
        if item.get("category") == "major" or item.get("symbol") in okx_symbols:
            filtered.append(item)
    return filtered


def load_watch_accounts() -> list[str]:
    try:
        import yaml
    except Exception:
        return []
    if not SOURCES_FILE.exists():
        return []
    cfg = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}
    return cfg.get("sources", {}).get("opentwitter", {}).get("watch_accounts", []) or []


def load_social_rules() -> dict:
    rules = json.loads(json.dumps(DEFAULT_SOCIAL_RULES, ensure_ascii=False))
    try:
        import yaml
    except Exception:
        return rules
    if not RULES_FILE.exists():
        return rules
    payload = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or {}
    social_rules = payload.get("social_rules", {}) or {}
    for key, value in social_rules.items():
        if value not in (None, {}, []):
            rules[key] = value
    return rules


def classify_social_risk(items: list[dict], rules: dict | None = None) -> str:
    rules = rules or load_social_rules()
    keywords = [str(x).lower() for x in rules.get("high_risk_keywords", [])]
    if not items:
        return "low"
    high_views = 0
    for item in items:
        try:
            views = int(item.get("viewCount", 0))
        except Exception:
            views = 0
        text = str(item.get("text", "")).lower()
        if views >= 50000 or any(k in text for k in keywords):
            high_views += 1
    if high_views >= 3:
        return "high"
    if high_views >= 1:
        return "medium"
    return "low"


def normalize_major_aliases(rules: dict) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for canonical, aliases in (rules.get("major_aliases", {}) or {}).items():
        canonical_symbol = str(canonical).upper()
        alias_map[canonical_symbol.upper()] = canonical_symbol
        for alias in aliases or []:
            alias_map[str(alias).upper()] = canonical_symbol
    return alias_map


def extract_symbols_from_text(text: str, rules: dict | None = None) -> list[str]:
    rules = rules or load_social_rules()
    alias_map = normalize_major_aliases(rules)
    ignore_tokens = {str(x).upper() for x in rules.get("symbol_ignore_tokens", [])}
    found: list[str] = []
    seen: set[str] = set()
    cleaned_text = re.sub(r"https?://\S+", " ", text)
    cleaned_text = re.sub(r"@[A-Za-z0-9_]+", " ", cleaned_text)
    upper_text = cleaned_text.upper()

    for alias, canonical in alias_map.items():
        if alias and alias in upper_text and canonical not in seen:
            found.append(canonical)
            seen.add(canonical)

    for token in re.findall(r"(?<![A-Za-z0-9])[$#]?([A-Za-z]{3,10})(?![A-Za-z0-9])", cleaned_text):
        upper = token.upper()
        if upper in ignore_tokens:
            continue
        canonical = alias_map.get(upper, upper)
        if canonical in seen:
            continue
        found.append(canonical)
        seen.add(canonical)
    return found


def classify_symbol_category(symbol: str, rules: dict | None = None) -> str:
    rules = rules or load_social_rules()
    major_symbols = {str(key).upper() for key in (rules.get("major_aliases", {}) or {}).keys()}
    return "major" if symbol.upper() in major_symbols else "meme"


def compute_weighted_heat(item: dict, rules: dict | None = None) -> int:
    rules = rules or load_social_rules()
    weights = rules.get("heat_weights", {}) or {}

    def as_int(value) -> int:
        try:
            return int(value or 0)
        except Exception:
            return 0

    return (
        as_int(item.get("viewCount")) * int(weights.get("view_count", 1))
        + as_int(item.get("favoriteCount")) * int(weights.get("favorite_count", 20))
        + as_int(item.get("replyCount")) * int(weights.get("reply_count", 30))
    )


def build_account_results(raw: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    account_results = []
    all_items = []
    for username, result in raw.items():
        items = result.get("data", []) if isinstance(result, dict) else []
        sanitized_items = [sanitize_tweet_item(item) for item in items if isinstance(item, dict)]
        if isinstance(result, dict):
            result["data"] = sanitized_items
        all_items.extend(sanitized_items)
        latest = sanitized_items[0] if sanitized_items else {}
        account_results.append(
            {
                "username": username,
                "latest_tweet_id": latest.get("id"),
                "latest_text": latest.get("text", "")[:180],
                "followers": latest.get("userFollowers"),
            }
        )
    return account_results, all_items


def build_symbol_mentions(all_items: list[dict], rules: dict | None = None) -> list[dict]:
    rules = rules or load_social_rules()
    mention_stats: dict[str, dict] = defaultdict(lambda: {
        "symbol": "",
        "category": "meme",
        "mention_count": 0,
        "weighted_heat": 0,
        "accounts": set(),
    })

    for item in all_items:
        symbols = extract_symbols_from_text(str(item.get("text", "")), rules)
        if not symbols:
            continue
        heat = compute_weighted_heat(item, rules)
        account = str(item.get("userScreenName") or "")
        for symbol in symbols:
            entry = mention_stats[symbol]
            entry["symbol"] = symbol
            entry["category"] = classify_symbol_category(symbol, rules)
            entry["mention_count"] += 1
            entry["weighted_heat"] += heat
            if account:
                entry["accounts"].add(account)

    results = []
    for symbol, entry in mention_stats.items():
        results.append(
            {
                "symbol": symbol,
                "category": entry["category"],
                "mention_count": entry["mention_count"],
                "unique_accounts": len(entry["accounts"]),
                "weighted_heat": entry["weighted_heat"],
            }
        )
    return sorted(results, key=lambda x: (-x["weighted_heat"], -x["mention_count"], x["symbol"]))


def infer_market_narrative(items: list[dict], symbol_mentions: list[dict] | None = None) -> str:
    if not items:
        return "unknown"
    mentions = symbol_mentions or []
    total_mentions = sum(item.get("mention_count", 0) for item in mentions)
    if len(mentions) >= 3 or total_mentions >= 5:
        return "active"
    if mentions:
        return "mixed"
    return "quiet"


def build_social_payload(raw: dict[str, dict], account_results: list[dict], all_items: list[dict], errors: dict[str, str], rules: dict | None = None, okx_symbols: set[str] | None = None) -> dict:
    rules = rules or load_social_rules()
    symbol_mentions = build_symbol_mentions(all_items, rules)
    filtered_mentions = filter_symbol_mentions_by_okx_symbols(symbol_mentions, okx_symbols)
    return {
        "market_narrative": infer_market_narrative(all_items, filtered_mentions),
        "watch_accounts": account_results,
        "social_risk": classify_social_risk(all_items, rules),
        "symbol_mentions": filtered_mentions,
        "top_discussed_symbols": [item["symbol"] for item in filtered_mentions[:5]],
        "raw": raw,
        "errors": errors,
    }


def main() -> None:
    token = get_env("TWITTER_TOKEN")
    if not token:
        path = write_raw_cache("opentwitter_cache.json", SOURCE, "error", {}, error="TWITTER_TOKEN missing")
        result_error(SOURCE, f"TWITTER_TOKEN missing, cache written to {path}")
        return

    accounts = load_watch_accounts()
    rules = load_social_rules()
    if not accounts:
        data = {
            "market_narrative": "unknown",
            "watch_accounts": [],
            "social_risk": "low",
            "symbol_mentions": [],
            "top_discussed_symbols": [],
            "raw": {},
        }
        path = write_raw_cache("opentwitter_cache.json", SOURCE, "ok", data)
        result_ok(path, SOURCE, {"watch_accounts": 0, "note": "whitelist empty"})
        return

    raw = {}
    errors = {}
    okx_symbols = None
    try:
        okx_symbols = fetch_okx_tradable_symbols()
    except Exception as exc:
        errors["okx_symbol_universe"] = str(exc)
    for username in accounts:
        try:
            payload = {"username": username, "maxResults": 5, "product": "Latest", "includeReplies": False, "includeRetweets": False}
            result = fetch_json(f"{BASE_URL}/open/twitter_user_tweets", payload, token)
            raw[username] = result
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors[username] = str(exc)

    account_results, all_items = build_account_results(raw)
    data = build_social_payload(raw=raw, account_results=account_results, all_items=all_items, errors=errors, rules=rules, okx_symbols=okx_symbols)
    status = "ok" if not errors else "partial"
    path = write_raw_cache("opentwitter_cache.json", SOURCE, status, data, error=json.dumps(errors, ensure_ascii=False) if errors else None)
    result_ok(path, SOURCE, {"watch_accounts": len(account_results), "status": status, "errors": errors, "top_discussed_symbols": data["top_discussed_symbols"]})


if __name__ == "__main__":
    main()
