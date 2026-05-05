#!/usr/bin/env python3
"""
Phase 3B context cache builder.

- Reads normalized raw cache files from context/raw/
- Aggregates them into context/context_cache.json
- Applies simple staleness and health logic
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
CONTEXT_DIR = BASE_DIR / "context"
RAW_DIR = CONTEXT_DIR / "raw"

SOURCES_FILE = CONFIG_DIR / "phase3_sources.yaml"
RULES_FILE = CONFIG_DIR / "phase3_rules.yaml"
FINAL_CACHE_FILE = CONTEXT_DIR / "context_cache.json"
NEWS_EVENT_STATE_FILE = CONTEXT_DIR / "news_event_state.json"

RAW_FILES = {
    "jin10": RAW_DIR / "jin10_cache.json",
    "blockbeats": RAW_DIR / "blockbeats_cache.json",
    "cmc": RAW_DIR / "cmc_cache.json",
    "moss_xsignal": RAW_DIR / "moss_xsignal_cache.json",
    "okx_market": RAW_DIR / "okx_market_cache.json",
    "okx_positions": RAW_DIR / "okx_positions_cache.json",
    "okx_news": RAW_DIR / "okx_news_cache.json",
    "opennews": RAW_DIR / "opennews_cache.json",
    "opentwitter": RAW_DIR / "opentwitter_cache.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def default_context() -> Dict[str, Any]:
    return {
        "generated_at": None,
        "schema_version": 1,
        "macro": {
            "updated_at": None,
            "regime": "unknown",
            "regime_bias": "unknown",
            "risk_state": "unknown",
            "geo_risk": "unknown",
            "event_window": False,
            "event_pre_release": False,
            "event_recent_release": False,
            "usd_strength": "unknown",
            "us10y_pressure": "unknown",
            "m2_trend": "unknown",
            "fear_greed_classification": "unknown",
            "fear_greed_value": None,
            "moss_sentiment_today": None,
            "moss_sentiment_bias": "unknown",
            "altcoin_season_classification": "unknown",
            "altcoin_season_value": None,
            "market_breadth": "unknown",
            "large_cap_leadership": "unknown",
            "macro_summary": [],
            "summary_buckets": {
                "geo": [],
                "macro_financial": [],
                "us_equity_sentiment": [],
            },
            "crypto_native_risk_summary": [],
            "sources": [],
        },
        "crypto_news": {
            "updated_at": None,
            "market_bias": "unknown",
            "news_risk": "unknown",
            "high_impact_events": [],
            "new_high_impact_events": [],
            "watchlist_events": [],
            "security_events": [],
            "sources": [],
        },
        "holdings": {
            "updated_at": None,
            "has_positions": False,
            "prioritized_symbols": [],
            "live_symbols": [],
            "demo_symbols": [],
            "sources": [],
        },
        "social": {
            "updated_at": None,
            "market_narrative": "unknown",
            "watch_accounts": [],
            "social_risk": "unknown",
            "symbol_mentions": [],
            "top_discussed_symbols": [],
            "holdings_symbol_mentions": [],
            "holdings_top_discussed_symbols": [],
            "okx_top_gainers": [],
            "okx_top_oi": [],
            "okx_oi_change": [],
            "okx_gainer_symbols": [],
            "okx_top_oi_symbols": [],
            "okx_oi_change_symbols": [],
            "cmc_trending_symbols": [],
            "moss_available_dates": [],
            "sources": [],
        },
        "market_context": {
            "updated_at": None,
            "btc_etf_flow": "unknown",
            "stablecoin_liquidity": "unknown",
            "onchain_tx_trend": "unknown",
            "contract_oi_environment": "unknown",
            "sentiment_indicator": "unknown",
            "fear_greed_classification": "unknown",
            "fear_greed_value": None,
            "altcoin_season_classification": "unknown",
            "altcoin_season_value": None,
            "market_breadth": "unknown",
            "large_cap_leadership": "unknown",
            "sources": [],
        },
        "macro_context": {
            "updated_at": None,
            "regime": "unknown",
            "regime_bias": "unknown",
            "risk_state": "unknown",
            "geo_risk": "unknown",
            "event_window": False,
            "summary": [],
            "summary_buckets": {
                "geo": [],
                "macro_financial": [],
                "us_equity_sentiment": [],
            },
        },
        "security": {
            "updated_at": None,
            "events": [],
        },
        "signal_inputs": {
            "holdings_related_new_events": [],
            "held_symbol_risk_events": [],
            "held_symbol_social_heat": [],
            "us_equity_risk_events": [],
            "security_events": [],
        },
        "market_state": {
            "updated_at": None,
            "market_sentiment": "unknown",
            "sentiment_confidence": 0.0,
            "risk_state": "unknown",
            "geo_risk": "unknown",
            "event_window": False,
            "macro_drivers": [],
            "crypto_native_risk_drivers": [],
            "summary": [],
        },
        "holdings_state": {
            "has_positions": False,
            "prioritized_symbols": [],
            "symbol_risk": [],
        },
        "hot_symbols_state": {
            "updated_at": None,
            "top_tradeable_symbols": [],
        },
        "health": {
            "jin10": "unknown",
            "blockbeats": "unknown",
            "cmc": "unknown",
            "moss_xsignal": "unknown",
            "okx_market": "unknown",
            "okx_positions": "unknown",
            "okx_news": "unknown",
            "opennews": "unknown",
            "opentwitter": "unknown",
        },
    }


def source_health(payload: Dict[str, Any], module: str, stale_rules: Dict[str, int]) -> str:
    status = payload.get("status", "unknown")
    if status in {"error", "hermes_only"}:
        return status
    updated_at = parse_ts(payload.get("updated_at"))
    if not updated_at:
        return "unknown"
    minutes = stale_rules.get(module)
    if not minutes:
        return status
    age_minutes = (datetime.now(timezone.utc) - updated_at).total_seconds() / 60
    if age_minutes > minutes:
        return "stale"
    return status or "ok"


def choose_bias(values: list[str]) -> str:
    filtered = [v for v in values if v and v != "unknown"]
    if not filtered:
        return "unknown"
    priority = ["bearish", "slightly_bearish", "mixed", "neutral", "slightly_bullish", "bullish"]
    scores = {v: filtered.count(v) for v in set(filtered)}
    return max(scores.keys(), key=lambda x: (scores[x], priority.index(x) if x in priority else -1))


def choose_ordered_level(values: list[str], order: list[str]) -> str:
    filtered = [v for v in values if v and v != "unknown"]
    if not filtered:
        return "unknown"
    rank = {value: idx for idx, value in enumerate(order)}
    return max(filtered, key=lambda value: rank.get(value, -1))


def unique_nonempty_strings(values: list[str], limit: int | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


def normalize_event_fingerprint(event: Dict[str, Any]) -> str:
    for key in ["id", "newsId", "fingerprint"]:
        value = str(event.get(key) or "").strip().lower()
        if value:
            return value
    title = " ".join(str(event.get("title") or "").lower().split())
    if title:
        return title
    source = str(event.get("source") or "unknown").strip().lower()
    return source


def extract_event_symbols(event: Dict[str, Any]) -> list[str]:
    explicit_symbols = [
        str(item).upper().strip()
        for item in (event.get("symbols") or [])
        if str(item).strip()
    ]
    corpus_parts = [
        str(event.get("title") or ""),
        str(event.get("summary") or ""),
        str(event.get("source") or ""),
    ]
    corpus = " ".join(part for part in corpus_parts if part)
    symbols: list[str] = []
    seen: set[str] = set()
    ignore_tokens = {
        "ETF", "SEC", "CPI", "PPI", "PCE", "FOMC", "NFP", "ADP", "GDP", "PMI", "ISM",
        "USD", "USDT", "USDC", "FDUSD", "DAI", "UST", "TVL", "DEX", "DAO", "API", "APP",
        "HTTP", "HTTPS", "HTML", "JSON", "UTC", "EU", "UK", "US",
    }

    def add_symbol(symbol: str) -> None:
        upper_symbol = str(symbol).upper().strip()
        if not upper_symbol or upper_symbol in seen or upper_symbol in ignore_tokens:
            return
        seen.add(upper_symbol)
        symbols.append(upper_symbol)

    for symbol in explicit_symbols:
        add_symbol(symbol)

    for match in re.finditer(r"(?<![A-Za-z0-9])[A-Z][A-Z0-9]{1,9}(?![A-Za-z0-9])", corpus):
        add_symbol(match.group(0))
    return symbols


def extract_symbols_from_event(event: Dict[str, Any]) -> list[str]:
    return extract_event_symbols(event)


def impact_to_level(event: Dict[str, Any]) -> str:
    raw = str(event.get("impact") or event.get("importance") or "unknown").strip().lower()
    if raw in {"high", "medium", "low"}:
        return raw
    if raw in {"bullish", "bearish", "neutral", "mixed"}:
        return "high"
    return "unknown"


def event_importance(event: Dict[str, Any]) -> str:
    return impact_to_level(event)



def text_contains_keyword(text: str, keyword: str) -> bool:
    normalized_text = str(text or "").lower()
    normalized_keyword = str(keyword or "").strip().lower()
    if not normalized_text or not normalized_keyword:
        return False
    if re.fullmatch(r"[a-z0-9& .+-]+", normalized_keyword):
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_keyword)}(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
    return normalized_keyword in normalized_text



def text_contains_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(text_contains_keyword(text, keyword) for keyword in keywords)



def event_mentions_symbol(event: Dict[str, Any], symbol: str) -> bool:
    target = str(symbol or "").upper().strip()
    if not target:
        return False
    symbols = {str(item).upper().strip() for item in (event.get("symbols") or []) if str(item).strip()}
    if target in symbols:
        return True
    for field in ["title", "summary", "source"]:
        if text_contains_keyword(str(event.get(field) or ""), target):
            return True
    return False



def classify_event_domains(text: str, source: str | None = None) -> list[str]:
    normalized = (text or "").strip().lower()
    if not normalized:
        return ["noise"]

    security_terms = [
        "exploit", "hack", "hacked", "attacker", "drain", "drains", "bridge exploit",
        "被盗", "黑客", "漏洞", "攻击", "draining funds",
    ]
    explicit_macro_terms = [
        "white house", "白宫", "美联储", "fomc", "鲍威尔", "powell", "cpi", "core cpi", "ppi", "pce", "core pce", "非农", "nfp",
        "失业率", "失业", "jobless claims", "initial jobless claims", "jolts", "adp", "利率", "rate cut", "rate hike", "dot plot",
        "gdp", "pmi", "ism", "retail sales", "通胀", "美债", "treasury yield", "2y yield", "10y yield", "收益率", "real yields", "美元指数", "dxy",
        "financial conditions", "jackson hole", "qe", "qt", "缩表", "量化宽松", "量化紧缩",
        "hormuz", "霍尔木兹", "iran", "伊朗", "israel", "以色列", "russia", "俄罗斯", "ukraine", "乌克兰",
        "停火", "ceasefire", "sanction", "制裁", "secondary sanctions", "swift", "tariff", "关税", "war", "战争", "航运风险", "原油", "欧佩克",
        "red sea", "红海", "bab el-mandeb", "曼德海峡", "suez", "苏伊士", "shipping disruption", "commercial vessel", "油轮遇袭", "商船遇袭",
        "refinery", "炼油厂", "supply disruption", "供应中断", "spr release", "战略石油储备释放", "crude supply",
        "trump", "特朗普", "日本央行", "日元", "boj", "ycc", "ecb", "boe", "pboc", "降准",
    ]
    us_equity_proxy_terms = [
        "美股开盘", "美股收盘", "美股盘初", "美股盘后", "美股盘前", "盘前", "盘后", "盘初", "尾盘", "午盘", "盘中", "us open", "us close", "after us open",
        "美股期货", "股指期货", "纳斯达克", "纳指", "nasdaq", "nasdaq futures", "纳指期货", "nq", "nq1!", "ndx",
        "标普500", "s&p 500", "spx", "spy", "qqq", "es", "es1!", "vix", "恐慌指数", "波动率指数", "russell 2000", "罗素2000", "iwm", "rut", "三大股指",
        "crcl", "circle", "bmnr", "mstr", "hood", "mara", "riot", "clsk", "cifr", "hut", "iren", "btdr", "corz", "wulf", "bitf",
        "ibit", "fbtc", "arkb", "bitb", "hodl", "gbtc", "etha", "feth", "coin rally", "coin shares", "crypto beta names",
    ]
    weak_macro_noise_terms = [
        "gamefi", "web3游戏", "百万英热", "天然气期货日内", "现报", "烧掉",
        "立即观看", "正在讲解中", "直播", "苹果", "英伟达", "nvidia", "apple",
        "金十图示", "中国金龙指数",
    ]
    regulation_terms = [
        "sec", "lawsuit", "起诉", "调查", "冻结", "freeze", "freezes", "law-enforcement", "执法", "compliance",
        "监管", "tether freezes", "usdt freeze",
    ]
    institutional_terms = [
        "etf", "blackrock", "fidelity", "strategy", "microstrategy", "institutional", "corporate treasury", "bitcoin treasury", "inflow", "outflow",
    ]
    crypto_native_terms = [
        "whale", "鲸鱼", "dormant whale", "protocol upgrade", "mainnet", "listing", "上线", "回购", "buyback",
        "airdrop", "token unlock", "生态", "链上", "wallet", "accumulates", "buys", "买入", "增持",
    ]
    flow_terms = [
        "exchange inflow", "exchange outflow", "netflow", "资金流", "转入交易所", "转出交易所", "stablecoin liquidity",
        "cex had a net outflow", "coinbase bitcoin premium", "reserves fell",
    ]

    if text_contains_any_keyword(normalized, weak_macro_noise_terms):
        return ["noise"]

    matches: list[str] = []
    ordered_rules = [
        ("security", security_terms),
        ("regulation", regulation_terms),
        ("flow", flow_terms),
        ("geo", us_equity_proxy_terms),
        ("institutional", institutional_terms),
        ("crypto_native", crypto_native_terms),
        ("geo", explicit_macro_terms),
    ]
    for domain, keywords in ordered_rules:
        if text_contains_any_keyword(normalized, keywords) and domain not in matches:
            matches.append(domain)

    return matches or ["noise"]



def classify_event_domain(text: str, source: str | None = None) -> str:
    return classify_event_domains(text, source=source)[0]



def is_macro_summary_candidate(title: str, macro_rules: Dict[str, Any] | None = None) -> bool:
    text = str(title or "").strip()
    if not text:
        return False
    rules = macro_rules or {}
    relevance_keywords = [str(item).strip().lower() for item in (rules.get("macro_summary_relevance_keywords", []) or []) if str(item).strip()]
    exclude_keywords = [str(item).strip().lower() for item in (rules.get("macro_summary_exclude_keywords", []) or []) if str(item).strip()]
    normalized = text.lower()
    if exclude_keywords and text_contains_any_keyword(normalized, exclude_keywords):
        return False
    if relevance_keywords:
        return text_contains_any_keyword(normalized, relevance_keywords)
    return True



def compress_macro_title(title: str) -> str:
    text = str(title or "").strip()
    if not text:
        return ""
    if text.startswith("【") and "】" in text:
        headline = text[1:text.index("】")].strip()
        if headline:
            return headline
    if "金十数据" in text and "讯，" in text:
        tail = text.split("讯，", 1)[-1].strip()
        if tail:
            return tail[:80].rstrip("。.;；，,")
    return text



def classify_macro_bucket(event: Dict[str, Any]) -> str:
    subtype = str(event.get("event_subtype") or "").strip().lower()
    title = str(event.get("title") or "").strip().lower()
    if subtype == "us_equity_risk_sentiment" or text_contains_any_keyword(title, ["纳斯达克", "nasdaq", "标普500", "s&p 500", "qqq", "spy", "美股", "us open", "us close", "mstr", "crcl", "bmnr", "bitcoin holdings"]):
        return "us_equity_sentiment"
    if subtype in {"macro_rates", "cpi", "fomc"} or text_contains_any_keyword(title, ["收益率", "美元指数", "美债", "利率", "cpi", "ppi", "pce", "非农", "失业", "美联储"]):
        return "macro_financial"
    return "geo"



def build_macro_summary_view(events: list[Dict[str, Any]], limit: int = 10) -> Dict[str, Any]:
    bucket_order = ["geo", "macro_financial", "us_equity_sentiment"]
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for event in events:
        compressed_title = compress_macro_title(event.get("title") or "")
        if not compressed_title:
            continue
        bucket = classify_macro_bucket({**event, "title": compressed_title})
        key = (bucket, compressed_title)
        current = deduped.get(key)
        candidate = {**event, "title": compressed_title, "macro_bucket": bucket}
        if current is None:
            deduped[key] = candidate
            continue
        current_score = float(current.get("event_score") or 0)
        candidate_score = float(candidate.get("event_score") or 0)
        if len(compressed_title) < len(str(current.get("title") or "")) or candidate_score > current_score:
            deduped[key] = candidate

    buckets: dict[str, list[str]] = {bucket: [] for bucket in bucket_order}
    for bucket in bucket_order:
        bucket_events = [event for event in deduped.values() if event.get("macro_bucket") == bucket]
        bucket_events.sort(key=lambda item: float(item.get("event_score") or 0), reverse=True)
        buckets[bucket] = [str(event.get("title") or "").strip() for event in bucket_events if str(event.get("title") or "").strip()]

    summary: list[str] = []
    for bucket in bucket_order:
        for title in buckets[bucket]:
            if title in summary:
                continue
            summary.append(title)
            if len(summary) >= limit:
                break
        if len(summary) >= limit:
            break
    return {"summary": summary, "buckets": buckets}


def classify_event_subtype(text: str, domain: str | None = None) -> str:
    semantic_domain = domain or classify_event_domain(text)
    return classify_event_subtypes(text, domains=[semantic_domain])[0]



def classify_event_subtypes(text: str, domains: list[str] | None = None) -> list[str]:
    normalized = (text or "").strip().lower()
    semantic_domains = domains or classify_event_domains(normalized)

    subtype_rules = [
        ("security", [("exploit", "exploit"), ("hack", "hack"), ("bridge", "bridge_exploit"), ("drain", "fund_drain")]),
        ("geo", [("hormuz", "shipping_risk"), ("霍尔木兹", "shipping_risk"), ("停火", "ceasefire"), ("特朗普", "state_policy"), ("trump", "state_policy"), ("fomc", "fomc"), ("cpi", "cpi")]),
        ("regulation", [("freeze", "asset_freeze"), ("冻结", "asset_freeze"), ("law-enforcement", "law_enforcement_action"), ("执法", "law_enforcement_action")]),
        ("institutional", [("etf", "etf_flow"), ("blackrock", "etf_flow"), ("treasury", "treasury_action"), ("strategy", "treasury_action"), ("inflow", "etf_flow"), ("outflow", "etf_flow")]),
        ("flow", [("exchange inflow", "exchange_inflow"), ("exchange outflow", "exchange_outflow"), ("netflow", "exchange_flow")]),
        ("crypto_native", [("whale", "whale_activity"), ("鲸鱼", "whale_activity"), ("dormant", "whale_activity"), ("upgrade", "protocol_upgrade"), ("listing", "listing")]),
    ]
    subtypes: list[str] = []
    for semantic_domain in semantic_domains:
        matched_subtype = semantic_domain or "unknown"
        for rule_domain, rules in subtype_rules:
            if semantic_domain != rule_domain:
                continue
            for marker, subtype in rules:
                if marker in normalized:
                    matched_subtype = subtype
                    break
            break
        if matched_subtype not in subtypes:
            subtypes.append(matched_subtype)
    return subtypes or ["unknown"]



def normalize_raw_event(
    event: Dict[str, Any],
    *,
    source: str,
    source_type: str,
    holdings_symbols: list[str],
    previous_state: Dict[str, Any],
    now: datetime,
) -> Dict[str, Any]:
    normalized_source = str(event.get("source") or source or "unknown").strip().lower() or "unknown"
    title = str(event.get("title") or event.get("headline") or event.get("summary") or "").strip()
    summary = str(event.get("summary") or event.get("content") or "").strip()
    merged_text = " ".join(part for part in [title, summary] if part)
    semantic_domains = classify_event_domains(merged_text, source=normalized_source)
    semantic_domain = semantic_domains[0]
    semantic_subtypes = classify_event_subtypes(merged_text, domains=semantic_domains)
    semantic_subtype = semantic_subtypes[0]
    normalized = normalize_news_event(
        {
            **event,
            "title": title,
            "summary": summary,
            "source": normalized_source,
            "importance": impact_to_level(event),
        },
        holdings_symbols=holdings_symbols,
        previous_state=previous_state,
        now=now,
    )
    return {
        **normalized,
        "source": normalized_source,
        "source_type": str(source_type or "unknown").strip().lower() or "unknown",
        "summary": summary,
        "symbols": extract_symbols_from_event({"title": title, "summary": summary, "source": normalized_source}),
        "event_domain": semantic_domain,
        "event_domains": semantic_domains,
        "event_subtype": semantic_subtype,
        "event_subtypes": semantic_subtypes,
        "importance": impact_to_level(event),
        "market_bias": str(event.get("market_bias") or "unknown").strip().lower() or "unknown",
        "raw_ref": {"id": str(event.get("id") or event.get("newsId") or normalized.get("fingerprint") or "")},
    }


def source_priority(source: str) -> int:
    mapping = {
        "okx_news": 3,
        "blockbeats": 3,
        "jin10_symbol_search": 2,
        "opennews": 1,
    }
    return mapping.get((source or "").strip().lower(), 0)


def freshness_score(published_at: str | None, now: datetime) -> int:
    published_dt = parse_ts(published_at)
    if not published_dt:
        return 0
    age_minutes = (now - published_dt).total_seconds() / 60
    if age_minutes < 0:
        return 0
    if age_minutes <= 30:
        return 4
    if age_minutes <= 120:
        return 3
    if age_minutes <= 360:
        return 2
    if age_minutes <= 1440:
        return 1
    return 0


def normalize_news_event(event: Dict[str, Any], holdings_symbols: list[str], previous_state: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    fingerprint = normalize_event_fingerprint(event)
    symbols = extract_event_symbols(event)
    held_set = {str(symbol).upper() for symbol in holdings_symbols if str(symbol).strip()}
    holds_match = any(symbol in held_set for symbol in symbols)
    prior = ((previous_state or {}).get("events", {}) or {}).get(fingerprint, {})
    novelty = "seen" if prior else "new"
    impact_level = impact_to_level(event)
    impact_weight = {"high": 3, "medium": 2, "low": 1, "unknown": 0}[impact_level]
    holdings_weight = 5 if holds_match else (2 if any(symbol in {"BTC", "ETH", "SOL"} for symbol in symbols) else 0)
    novelty_weight = 4 if novelty == "new" else -3
    source_weight = source_priority(str(event.get("source") or "unknown"))
    fresh_weight = freshness_score(event.get("published_at"), now)
    whale_boost_terms = ["whale", "鲸鱼", "dormant", "etf", "treasury", "inflow", "outflow", "增持", "减持", "买入", "卖出"]
    title = str(event.get("title") or "").strip()
    whale_boost = 2 if any(term.lower() in title.lower() for term in whale_boost_terms) else 0
    score = holdings_weight + novelty_weight + source_weight + fresh_weight + impact_weight + whale_boost
    return {
        **event,
        "fingerprint": fingerprint,
        "title": title,
        "symbols": symbols,
        "holds_match": holds_match,
        "novelty": novelty,
        "impact_level": impact_level,
        "event_score": float(score),
    }


def rank_news_events(
    events: list[Dict[str, Any]],
    holdings_symbols: list[str],
    previous_state: Dict[str, Any] | None = None,
    now: datetime | None = None,
) -> list[Dict[str, Any]]:
    current = now or datetime.now(timezone.utc)
    seen_fingerprints: set[str] = set()
    ranked: list[Dict[str, Any]] = []
    for event in events:
        normalized = normalize_news_event(event, holdings_symbols, previous_state or {}, current)
        fingerprint = normalized["fingerprint"]
        if fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)
        ranked.append(normalized)
    ranked.sort(key=lambda item: (item.get("event_score", 0), item.get("holds_match", False), item.get("novelty") == "new"), reverse=True)
    return ranked



def build_semantic_event_pool(
    raw_data: Dict[str, Dict[str, Any]],
    *,
    holdings_symbols: list[str],
    previous_state: Dict[str, Any] | None = None,
    now: datetime | None = None,
) -> list[Dict[str, Any]]:
    current = now or datetime.now(timezone.utc)
    prior_state = previous_state or {}
    raw_events: list[tuple[Dict[str, Any], str, str]] = []

    jin10_macro = ((raw_data.get("jin10", {}) or {}).get("data", {}) or {}).get("macro", {}) or {}
    for item in jin10_macro.get("macro_summary", []) or []:
        title = str(item or "").strip()
        if not title:
            continue
        raw_events.append(({"id": f"jin10:macro_summary:{title}", "title": title}, "jin10", "macro_summary"))

    blockbeats_data = ((raw_data.get("blockbeats", {}) or {}).get("data", {}) or {})
    for item in (((blockbeats_data.get("macro", {}) or {}).get("macro_summary", []) or [])):
        title = str(item or "").strip()
        if not title:
            continue
        raw_events.append(({"id": f"blockbeats:macro_summary:{title}", "title": title}, "blockbeats", "macro_summary"))
    for item in (((blockbeats_data.get("crypto_news", {}) or {}).get("high_impact_events", []) or [])):
        raw_events.append(({**item, "source": item.get("source") or "blockbeats"}, "blockbeats", "crypto_news"))

    okx_news = (((raw_data.get("okx_news", {}) or {}).get("data", {}) or {}).get("high_impact_events", []) or [])
    for item in okx_news:
        raw_events.append(({**item, "source": item.get("source") or "okx_news"}, "okx_news", "high_impact_events"))

    opennews_events = (((raw_data.get("opennews", {}) or {}).get("data", {}) or {}).get("high_impact_events", []) or [])
    for item in opennews_events:
        raw_events.append(({**item, "source": item.get("source") or "opennews"}, "opennews", "high_impact_events"))

    pool: list[Dict[str, Any]] = []
    seen_fingerprints: set[str] = set()
    for event, source, source_type in raw_events:
        normalized = normalize_raw_event(
            event,
            source=source,
            source_type=source_type,
            holdings_symbols=holdings_symbols,
            previous_state=prior_state,
            now=current,
        )
        fingerprint = normalized.get("fingerprint")
        if not fingerprint or fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)
        pool.append(normalized)

    pool.sort(key=lambda item: (item.get("event_score", 0), item.get("published_at") or ""), reverse=True)
    return pool


def load_news_event_state(path: Path = NEWS_EVENT_STATE_FILE) -> Dict[str, Any]:
    if not path.exists():
        return {"updated_at": None, "schema_version": 1, "events": {}}
    return load_json(path)


def update_news_event_state(previous_state: Dict[str, Any], ranked_events: list[Dict[str, Any]], now_iso: str) -> Dict[str, Any]:
    events_state = dict((previous_state or {}).get("events", {}) or {})
    for event in ranked_events:
        fingerprint = str(event.get("fingerprint") or "").strip()
        if not fingerprint:
            continue
        prior = events_state.get(fingerprint, {})
        first_seen_at = prior.get("first_seen_at") or now_iso
        seen_count = int(prior.get("seen_count") or 0) + 1
        events_state[fingerprint] = {
            "title": str(event.get("title") or ""),
            "source": str(event.get("source") or "unknown"),
            "symbols": event.get("symbols", []),
            "first_seen_at": first_seen_at,
            "last_seen_at": now_iso,
            "seen_count": seen_count,
            "last_score": float(event.get("event_score") or 0),
        }
    return {
        "updated_at": now_iso,
        "schema_version": 1,
        "events": events_state,
    }


def write_news_event_state(payload: Dict[str, Any], path: Path = NEWS_EVENT_STATE_FILE) -> None:
    write_json(path, payload)


def classify_security_event_state(text: str) -> str:
    normalized = (text or "").strip().lower()
    if not normalized:
        return "background"

    live_markers = [
        "draining",
        "drain funds",
        "drains funds",
        "ongoing exploit",
        "正在被攻击",
        "正在流出",
        "实时",
        "live exploit",
    ]
    followup_markers = [
        "launder",
        "laundering",
        "洗钱",
        "洗币",
        "转出",
        "moved funds",
        "move funds",
        "再度活跃",
        "沉寂",
        "completed",
        "完成",
    ]
    active_markers = [
        "hack",
        "hacked",
        "exploit",
        "attacker",
        "攻击响应",
        "response",
        "stolen",
        "breach",
        "incident",
        "被盗",
        "漏洞",
        "黑客",
    ]
    postmortem_markers = [
        "postmortem",
        "复盘",
        "总结",
        "patched",
        "patch deployed",
        "reimbursement",
        "赔付",
    ]
    background_markers = [
        "warn",
        "warning",
        "may rise",
        "threat",
        "risk in 2026",
        "趋势",
        "预警",
    ]

    if any(marker in normalized for marker in live_markers):
        return "live_exploit"
    if any(marker in normalized for marker in postmortem_markers):
        return "postmortem"
    if any(marker in normalized for marker in followup_markers):
        return "postmortem"
    if any(marker in normalized for marker in active_markers):
        return "post_exploit_active"
    if any(marker in normalized for marker in background_markers):
        return "background"
    return "background"


def event_has_domain(event: Dict[str, Any], domain: str) -> bool:
    target = str(domain or "").strip().lower()
    if not target:
        return False
    domains = event.get("event_domains")
    if isinstance(domains, list) and domains:
        normalized_domains = {str(item).strip().lower() for item in domains if str(item).strip()}
        if target in normalized_domains:
            return True
    return str(event.get("event_domain") or "").strip().lower() == target



def extract_security_events(events: list[dict[str, Any]], limit: int = 10) -> list[dict[str, str]]:
    security_events: list[dict[str, str]] = []
    for event in events:
        if not event_has_domain(event, "security"):
            continue
        title = str(event.get("title") or "").strip()
        state = classify_security_event_state(title)
        if state == "background":
            continue
        security_events.append(
            {
                "title": title,
                "source": str(event.get("source") or "unknown"),
                "state": state,
            }
        )
        if len(security_events) >= limit:
            break
    return security_events


def normalize_sentiment_indicator(value: str) -> str:
    mapping = {
        "positive": "slightly_bullish",
        "negative": "slightly_bearish",
        "neutral": "neutral",
        "bullish": "bullish",
        "bearish": "bearish",
        "slightly_bullish": "slightly_bullish",
        "slightly_bearish": "slightly_bearish",
        "mixed": "mixed",
        "unknown": "unknown",
    }
    return mapping.get((value or "unknown").strip().lower(), "unknown")


def classify_regime_bias(macro: Dict[str, Any], rules: Dict[str, Any] | None = None) -> str:
    usd_strength = str(macro.get("usd_strength", "unknown") or "unknown").strip().lower()
    if usd_strength not in {"weak", "neutral", "strong"}:
        usd_strength = "unknown"

    us10y_pressure = str(macro.get("us10y_pressure", "unknown") or "unknown").strip().lower()
    if us10y_pressure not in {"low", "medium", "high"}:
        us10y_pressure = "unknown"

    geo_risk = str(macro.get("geo_risk", "unknown") or "unknown").strip().lower()
    if geo_risk not in {"low", "medium", "high"}:
        geo_risk = "unknown"

    fear_greed = str(macro.get("fear_greed_classification", "unknown") or "unknown").strip().lower()
    if fear_greed not in {"extreme_fear", "fear", "neutral", "greed", "extreme_greed", "unknown"}:
        fear_greed = "unknown"

    market_breadth = str(macro.get("market_breadth", "unknown") or "unknown").strip().lower()
    if market_breadth not in {"broad_risk_on", "mixed", "broad_risk_off", "unknown"}:
        market_breadth = "unknown"

    moss_sentiment = macro.get("moss_sentiment_today")
    try:
        moss_sentiment = float(moss_sentiment) if moss_sentiment is not None else None
    except Exception:
        moss_sentiment = None

    core_known = any(value != "unknown" for value in [usd_strength, us10y_pressure, geo_risk, fear_greed, market_breadth]) or moss_sentiment is not None
    if not core_known:
        return "unknown"

    score = 0.0
    score += {"weak": 1, "neutral": 0, "strong": -1}.get(usd_strength, 0)
    score += {"low": 1, "medium": 0, "high": -1}.get(us10y_pressure, 0)
    score += {"low": 0.5, "medium": 0, "high": -1}.get(geo_risk, 0)
    if bool(macro.get("event_window")):
        score -= 0.5
    score += {
        "extreme_fear": -1.5,
        "fear": -1,
        "neutral": 0,
        "greed": 1,
        "extreme_greed": 1.5,
    }.get(fear_greed, 0)
    score += {"broad_risk_on": 1.5, "mixed": 0, "broad_risk_off": -1.5}.get(market_breadth, 0)

    if moss_sentiment is not None:
        if moss_sentiment >= 65:
            score += 1.5
        elif moss_sentiment >= 55:
            score += 1
        elif moss_sentiment >= 45:
            score += 0
        elif moss_sentiment >= 35:
            score -= 1
        else:
            score -= 1.5

    if score >= 2:
        return "bullish"
    if score <= -2:
        return "bearish"
    return "neutral"


def risk_state_has_extreme_trigger(macro: Dict[str, Any], crypto_news: Dict[str, Any]) -> bool:
    security_events = crypto_news.get("security_events", []) or []
    if any(str(event.get("state") or event.get("event_state") or "").strip().lower() == "live_exploit" for event in security_events):
        return True
    return False


def classify_risk_state(payload: Dict[str, Any], rules: Dict[str, Any] | None = None) -> str:
    geo_risk = str(payload.get("geo_risk", "unknown") or "unknown").strip().lower()
    geo_risk_has_shock = bool(payload.get("geo_risk_has_shock"))
    if geo_risk not in {"low", "medium", "high"}:
        geo_risk = "unknown"

    news_risk = str(payload.get("news_risk", "unknown") or "unknown").strip().lower()
    if news_risk not in {"low", "medium", "high"}:
        news_risk = "unknown"

    fear_greed = str(payload.get("fear_greed_classification", "unknown") or "unknown").strip().lower()
    if fear_greed not in {"extreme_fear", "fear", "neutral", "greed", "extreme_greed", "unknown"}:
        fear_greed = "unknown"

    moss_sentiment = payload.get("moss_sentiment_today")
    try:
        moss_sentiment = float(moss_sentiment) if moss_sentiment is not None else None
    except Exception:
        moss_sentiment = None

    security_events = payload.get("security_events", []) or []
    core_known = any(value != "unknown" for value in [geo_risk, news_risk, fear_greed]) or bool(payload.get("event_pre_release")) or bool(payload.get("event_recent_release")) or bool(security_events) or moss_sentiment is not None
    if not core_known:
        return "unknown"

    score = 0.0
    score += {"low": 0, "medium": 1, "high": 3}.get(geo_risk, 0)
    if bool(payload.get("event_pre_release")):
        score += 2
    if bool(payload.get("event_recent_release")):
        score += 1
    score += {"low": 0, "medium": 1.5, "high": 3}.get(news_risk, 0)

    security_states = [str(event.get("state") or event.get("event_state") or "").strip().lower() for event in security_events]
    if "live_exploit" in security_states:
        score += 4
    elif "post_exploit_active" in security_states:
        score += 2
    elif security_states and all(state == "postmortem" for state in security_states if state):
        score += 0.5

    if moss_sentiment is not None:
        if moss_sentiment >= 75 or moss_sentiment <= 25:
            score += 1
        elif 65 <= moss_sentiment <= 74 or 26 <= moss_sentiment <= 35:
            score += 0.5

    score += {
        "extreme_fear": 1,
        "fear": 0.5,
        "neutral": 0,
        "greed": 0.5,
        "extreme_greed": 1,
    }.get(fear_greed, 0)

    if risk_state_has_extreme_trigger(payload, payload):
        return "extreme"
    if geo_risk_has_shock and news_risk == "high" and (
        bool(payload.get("event_pre_release"))
        or bool(payload.get("event_recent_release"))
        or fear_greed in {"fear", "extreme_fear", "greed", "extreme_greed"}
        or score >= 9
    ):
        return "extreme"
    if score >= 11 and geo_risk_has_shock:
        return "extreme"
    if score <= 2:
        return "low"
    if score <= 8:
        return "medium"
    if score <= 10:
        return "high"
    return "high"


def classify_macro_regime(macro: Dict[str, Any], rules: Dict[str, Any] | None = None) -> str:
    return classify_regime_bias(macro, rules)


def compute_sentiment_confidence(market_sentiment: str, macro: Dict[str, Any]) -> float:
    sentiment = str(market_sentiment or "unknown").strip().lower()
    if sentiment == "unknown":
        return 0.0
    known_values = 0
    for value in [
        macro.get("usd_strength"),
        macro.get("us10y_pressure"),
        macro.get("geo_risk"),
        macro.get("fear_greed_classification"),
        macro.get("market_breadth"),
    ]:
        if str(value or "unknown").strip().lower() != "unknown":
            known_values += 1
    if macro.get("moss_sentiment_today") is not None:
        known_values += 1
    return round(min(1.0, known_values / 3), 2)


def derive_news_risk(ranked_events: list[Dict[str, Any]], security_events: list[Dict[str, Any]]) -> str:
    security_states = [str(event.get("state") or event.get("event_state") or "").strip().lower() for event in (security_events or [])]
    if "live_exploit" in security_states or "post_exploit_active" in security_states:
        return "high"

    total_score = 0.0
    seen_titles: set[str] = set()
    systemic_keywords = [
        "etf", "bitcoin", "btc", "ethereum", "eth", "stablecoin", "usdt", "usdc", "tether",
        "binance", "coinbase", "exchange", "交易所", "市场", "比特币", "以太坊", "稳定币", "美联储",
    ]
    severe_keywords = [
        "exploit", "hack", "drain", "breach", "blacklist", "freeze", "lawsuit", "delist", "depeg",
        "黑客", "被盗", "漏洞", "冻结", "起诉", "脱锚",
    ]
    for event in ranked_events[:10]:
        raw_title = str(event.get("title") or "").strip()
        title = raw_title.lower()
        if not raw_title or raw_title in seen_titles:
            continue
        seen_titles.add(raw_title)
        domains = {str(domain).strip().lower() for domain in (event.get("event_domains") or [event.get("event_domain")]) if str(domain).strip()}
        novelty = str(event.get("novelty") or "").strip().lower()
        market_bias = str(event.get("market_bias") or "").strip().lower()
        holds_match = bool(event.get("holds_match"))
        is_systemic = holds_match or any(keyword in title for keyword in systemic_keywords)
        score = 0.0
        if any(keyword in title for keyword in severe_keywords):
            score += 4 if is_systemic else 0.5
        if "security" in domains:
            score += 3 if is_systemic else 1.5
        elif "regulation" in domains:
            score += 2 if is_systemic else 0.5
        elif "flow" in domains:
            score += 1 if market_bias in {"bearish", "slightly_bearish"} else 0
        if market_bias in {"bearish", "slightly_bearish"}:
            score += 1
        if novelty == "new" and score > 0:
            score += 0.5
        if holds_match:
            score += 1
        if market_bias in {"bullish", "slightly_bullish"} and domains <= {"institutional"}:
            score = max(0.0, score - 2)
        total_score += score

    if total_score >= 6:
        return "high"
    if total_score >= 2:
        return "medium"
    return "low"


def build_market_state(ctx: Dict[str, Any]) -> Dict[str, Any]:
    macro = ctx.get("macro", {}) or {}
    market_sentiment = str(macro.get("regime_bias") or macro.get("regime") or "unknown")
    summary = list(macro.get("macro_summary", []) or [])
    return {
        "updated_at": macro.get("updated_at"),
        "market_sentiment": market_sentiment,
        "sentiment_confidence": compute_sentiment_confidence(market_sentiment, macro),
        "risk_state": str(macro.get("risk_state") or "unknown"),
        "geo_risk": str(macro.get("geo_risk") or "unknown"),
        "event_window": bool(macro.get("event_window")),
        "macro_drivers": unique_nonempty_strings(summary, limit=5),
        "crypto_native_risk_drivers": unique_nonempty_strings(list(macro.get("crypto_native_risk_summary", []) or []), limit=5),
        "summary": unique_nonempty_strings(summary, limit=5),
    }


def build_holdings_focused_social(ctx: Dict[str, Any]) -> Dict[str, Any]:
    holdings = ctx.get("holdings", {}) or {}
    social = ctx.get("social", {}) or {}
    held_symbols = {
        str(symbol).upper().strip()
        for symbol in (holdings.get("prioritized_symbols", []) or [])
        if str(symbol).strip()
    }
    holdings_symbol_mentions = [
        item for item in (social.get("symbol_mentions", []) or [])
        if str(item.get("symbol") or "").upper().strip() in held_symbols
    ]
    holdings_top_discussed_symbols = [
        str(symbol).upper().strip()
        for symbol in (social.get("top_discussed_symbols", []) or [])
        if str(symbol).strip() and str(symbol).upper().strip() in held_symbols
    ]
    return {
        "holdings_symbol_mentions": holdings_symbol_mentions,
        "holdings_top_discussed_symbols": holdings_top_discussed_symbols,
    }


def build_held_symbol_signal_inputs(
    ctx: Dict[str, Any],
    semantic_event_pool: list[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    holdings = ctx.get("holdings", {}) or {}
    crypto_news = ctx.get("crypto_news", {}) or {}
    social = ctx.get("social", {}) or {}
    held_symbols = [
        str(symbol).upper().strip()
        for symbol in (holdings.get("prioritized_symbols", []) or [])
        if str(symbol).strip()
    ]
    semantic_pool = semantic_event_pool or []
    held_symbol_risk_events = [
        event for event in semantic_pool
        if any(event_mentions_symbol(event, symbol) for symbol in held_symbols)
        and str(event.get("source_type") or "").strip().lower() != "macro_summary"
    ]
    if not held_symbol_risk_events:
        held_symbol_risk_events = [
            event for event in (crypto_news.get("high_impact_events", []) or [])
            if any(event_mentions_symbol(event, symbol) for symbol in held_symbols)
        ]
    holdings_related_new_events = [
        event for event in (crypto_news.get("new_high_impact_events", []) or [])
        if any(event_mentions_symbol(event, symbol) for symbol in held_symbols)
    ]
    held_symbol_social_heat = [
        item for item in (social.get("holdings_symbol_mentions", []) or [])
        if str(item.get("symbol") or "").upper().strip() in held_symbols
    ]
    return {
        "holdings_related_new_events": holdings_related_new_events,
        "held_symbol_risk_events": held_symbol_risk_events,
        "held_symbol_social_heat": held_symbol_social_heat,
    }


def build_holdings_state(ctx: Dict[str, Any]) -> Dict[str, Any]:
    holdings = ctx.get("holdings", {}) or {}
    crypto_news = ctx.get("crypto_news", {}) or {}
    social = ctx.get("social", {}) or {}
    global_risk = str((ctx.get("market_state", {}) or {}).get("risk_state") or "unknown").strip().lower()
    market_sentiment = str((ctx.get("market_state", {}) or {}).get("market_sentiment") or "unknown")
    symbol_mentions = {
        str(item.get("symbol") or "").upper().strip(): item
        for item in (social.get("symbol_mentions", []) or [])
        if str(item.get("symbol") or "").strip()
    }
    security_events = crypto_news.get("security_events", []) or []
    high_impact_events = crypto_news.get("high_impact_events", []) or []
    symbol_risk: list[Dict[str, Any]] = []
    for symbol in holdings.get("prioritized_symbols", []) or []:
        upper_symbol = str(symbol).upper().strip()
        if not upper_symbol:
            continue
        matching_security = [
            event for event in security_events
            if event_mentions_symbol(event, upper_symbol)
        ]
        semantic_live_security = [
            event for event in high_impact_events
            if event_has_domain(event, "security")
            and classify_security_event_state(str(event.get("title") or "")) == "live_exploit"
            and event_mentions_symbol(event, upper_symbol)
        ]
        relevant_events = [
            event for event in (crypto_news.get("new_high_impact_events", []) or [])
            if event_mentions_symbol(event, upper_symbol)
        ]
        social_item = symbol_mentions.get(upper_symbol, {})
        social_heat = int(social_item.get("weighted_heat", 0) or 0)

        reasons: list[str] = []
        risk_state = global_risk if global_risk in {"low", "medium", "high", "extreme"} else "unknown"
        if semantic_live_security or any(str(event.get("state") or "").strip().lower() == "live_exploit" for event in matching_security):
            risk_state = "extreme"
            reasons.append("held_symbol_live_security_event")
        elif len(relevant_events) >= 2:
            risk_state = "high"
            reasons.append("held_symbol_event_cluster")
        elif global_risk in {"medium", "high", "extreme"}:
            reasons.append(f"global_market_risk_{global_risk}")
        elif global_risk == "low":
            reasons.append("global_market_risk_low")
        if social_heat >= 80000:
            reasons.append("held_symbol_social_heat_elevated")

        symbol_risk.append(
            {
                "symbol": upper_symbol,
                "risk_state": risk_state,
                "relevant_event_count": len(relevant_events),
                "relevant_social_heat": social_heat,
                "macro_alignment": market_sentiment,
                "reasons": reasons,
            }
        )

    return {
        "has_positions": bool(holdings.get("has_positions", False)),
        "prioritized_symbols": list(holdings.get("prioritized_symbols", []) or []),
        "symbol_risk": symbol_risk,
    }


def build_top_tradeable_symbols(ctx: Dict[str, Any], limit: int = 10) -> list[Dict[str, Any]]:
    holdings = ctx.get("holdings", {}) or {}
    social = ctx.get("social", {}) or {}
    tradable_allowlist = {
        *[str(symbol).upper().strip() for symbol in (holdings.get("prioritized_symbols", []) or []) if str(symbol).strip()],
        *[str(symbol).upper().strip() for symbol in (social.get("cmc_trending_symbols", []) or []) if str(symbol).strip()],
        *[str(symbol).upper().strip() for symbol in (social.get("okx_gainer_symbols", []) or []) if str(symbol).strip()],
        *[str(symbol).upper().strip() for symbol in (social.get("okx_top_oi_symbols", []) or []) if str(symbol).strip()],
        *[str(symbol).upper().strip() for symbol in (social.get("okx_oi_change_symbols", []) or []) if str(symbol).strip()],
        "BTC",
        "ETH",
        "SOL",
    }
    symbol_mentions = {
        str(item.get("symbol") or "").upper().strip(): item
        for item in (social.get("symbol_mentions", []) or [])
        if str(item.get("symbol") or "").strip() and str(item.get("symbol") or "").upper().strip() in tradable_allowlist
    }
    ranking: dict[str, Dict[str, Any]] = {}

    def ensure(symbol: str) -> Dict[str, Any]:
        upper_symbol = symbol.upper().strip()
        entry = ranking.get(upper_symbol)
        if entry is None:
            entry = {
                "symbol": upper_symbol,
                "score": 0,
                "sources": [],
                "reasons": [],
            }
            ranking[upper_symbol] = entry
        return entry

    def add_score(symbol: str, score: int, source: str, reasons: list[str]) -> None:
        if not symbol or symbol.upper().strip() not in tradable_allowlist:
            return
        entry = ensure(symbol)
        entry["score"] += int(score)
        if source not in entry["sources"]:
            entry["sources"].append(source)
        for reason in reasons:
            if reason not in entry["reasons"]:
                entry["reasons"].append(reason)

    for symbol in holdings.get("prioritized_symbols", []) or []:
        add_score(str(symbol), 120, "holding", ["existing_holding"])

    top_discussed = {str(symbol).upper().strip() for symbol in (social.get("top_discussed_symbols", []) or []) if str(symbol).strip()}
    for symbol, item in symbol_mentions.items():
        unique_accounts = int(item.get("unique_accounts", 0) or 0)
        weighted_heat = int(item.get("weighted_heat", 0) or 0)
        if symbol in top_discussed and unique_accounts >= 2 and weighted_heat >= 100000:
            score = weighted_heat // 5000 + unique_accounts * 10 + 22
            reasons = ["high_social_heat", "multi_account_discussion"]
        else:
            score = weighted_heat // 5000 + unique_accounts * 2
            reasons = ["social_symbol_mention"]
        add_score(symbol, score, "social", reasons)

    for symbol in social.get("cmc_trending_symbols", []) or []:
        add_score(str(symbol), 12, "cmc", ["cmc_trending_symbol"])

    quadrant_bonus = {
        "oi_up_price_up": (26, ["okx_oi_price_up_quadrant", "okx_oi_change_leader"]),
        "oi_up_price_down": (18, ["okx_oi_short_build_quadrant", "okx_oi_change_leader"]),
        "oi_down_price_up": (14, ["okx_oi_short_cover_quadrant"]),
        "oi_down_price_down": (10, ["okx_oi_long_exit_quadrant"]),
    }
    for item in (social.get("okx_oi_change", []) or [])[:10]:
        symbol = str(item.get("symbol") or "")
        quadrant = str(item.get("quadrant") or "").strip()
        score, reasons = quadrant_bonus.get(quadrant, (12, ["okx_oi_change_leader"]))
        add_score(symbol, score, "okx_oi_change", reasons)

    for index, item in enumerate((social.get("okx_top_gainers", []) or [])[:10], start=1):
        score = max(8, 20 - index)
        add_score(str(item.get("symbol") or ""), score, "okx_top_gainers", ["okx_top_gainer_24h"])

    for index, item in enumerate((social.get("okx_top_oi", []) or [])[:10], start=1):
        score = max(6, 16 - index)
        add_score(str(item.get("symbol") or ""), score, "okx_top_oi", ["okx_top_oi_contract"])

    ranked = sorted(
        ranking.values(),
        key=lambda item: (-int(item.get("score", 0)), item.get("symbol", "")),
    )[:limit]
    return [
        {
            "symbol": item["symbol"],
            "score": int(item["score"]),
            "rank": index,
            "sources": list(item["sources"]),
            "reasons": list(item["reasons"]),
        }
        for index, item in enumerate(ranked, start=1)
    ]


def build_hot_symbols_state(ctx: Dict[str, Any]) -> Dict[str, Any]:
    updated_candidates = [
        (ctx.get("holdings", {}) or {}).get("updated_at"),
        (ctx.get("social", {}) or {}).get("updated_at"),
    ]
    return {
        "updated_at": max([value for value in updated_candidates if value], default=None),
        "top_tradeable_symbols": build_top_tradeable_symbols(ctx),
    }


def merge_context(
    raw_data: Dict[str, Dict[str, Any]],
    rules: Dict[str, Any],
    previous_news_state: Dict[str, Any] | None = None,
    now: datetime | None = None,
    return_news_state: bool = False,
) -> Dict[str, Any] | tuple[Dict[str, Any], Dict[str, Any]]:
    ctx = default_context()
    now_dt = now or datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    ctx["generated_at"] = now_iso

    stale_rules = rules.get("staleness_threshold_minutes", {}) or {}

    for source_name, payload in raw_data.items():
        if not payload:
            ctx["health"][source_name] = "missing"
        else:
            # map per-source health to module/source health
            if source_name == "blockbeats":
                module_name = "market_context"
            elif source_name == "cmc":
                module_name = "market_context"
            elif source_name == "okx_market":
                module_name = "social"
            elif source_name == "okx_positions":
                module_name = "holdings"
            elif source_name == "okx_news" or source_name == "opennews":
                module_name = "crypto_news"
            elif source_name == "opentwitter":
                module_name = "social"
            else:
                module_name = "macro"
            ctx["health"][source_name] = source_health(payload, module_name, stale_rules)

    holdings = raw_data.get("okx_positions", {}).get("data", {})
    ctx["holdings"].update({
        "updated_at": raw_data.get("okx_positions", {}).get("updated_at"),
        "has_positions": bool(holdings.get("has_positions", False)),
        "prioritized_symbols": holdings.get("prioritized_symbols", []),
        "live_symbols": ((holdings.get("accounts", {}) or {}).get("live", {}) or {}).get("symbols", []),
        "demo_symbols": ((holdings.get("accounts", {}) or {}).get("demo", {}) or {}).get("symbols", []),
        "sources": ["okx_positions"] if ctx["health"].get("okx_positions") not in {"missing", "error"} else [],
    })

    semantic_event_pool = build_semantic_event_pool(
        raw_data,
        holdings_symbols=ctx["holdings"].get("prioritized_symbols", []),
        previous_state=previous_news_state or {},
        now=now_dt,
    )

    # Phase 2: derive business-layer views from semantic domains rather than source buckets.
    bb = raw_data.get("blockbeats", {}).get("data", {})
    bb_macro = bb.get("macro", {})
    jin10_data = raw_data.get("jin10", {}).get("data", {})
    jin10_macro = jin10_data.get("macro", {})
    cmc = raw_data.get("cmc", {}).get("data", {})
    cmc_macro = cmc.get("macro", {}) if isinstance(cmc.get("macro", {}), dict) else {}
    cmc_ctx = cmc.get("market_context", {}) if isinstance(cmc.get("market_context", {}), dict) else {}
    moss = raw_data.get("moss_xsignal", {}).get("data", {})
    moss_macro = moss.get("macro", {}) if isinstance(moss.get("macro", {}), dict) else {}
    moss_social = moss.get("social", {}) if isinstance(moss.get("social", {}), dict) else {}
    macro_updated_candidates = [
        raw_data.get("blockbeats", {}).get("updated_at"),
        raw_data.get("cmc", {}).get("updated_at"),
        raw_data.get("moss_xsignal", {}).get("updated_at"),
        raw_data.get("jin10", {}).get("updated_at"),
    ]
    macro_domain_events = [
        event for event in semantic_event_pool
        if any(event_has_domain(event, domain) for domain in {"macro", "geo"})
        and is_macro_summary_candidate(event.get("title", ""), rules.get("macro_rules", {}))
    ]

    crypto_native_summary_events = [
        event for event in semantic_event_pool
        if any(event_has_domain(event, domain) for domain in {"crypto_native", "flow", "institutional", "regulation"})
    ]
    macro_summary_view = build_macro_summary_view(macro_domain_events, limit=10)
    ctx["macro"].update({
        "updated_at": max([x for x in macro_updated_candidates if x], default=None),
        "usd_strength": bb_macro.get("usd_strength", "unknown"),
        "us10y_pressure": bb_macro.get("us10y_pressure", "unknown"),
        "m2_trend": bb_macro.get("m2_trend", "unknown"),
        "fear_greed_classification": cmc_macro.get("fear_greed_classification", "unknown"),
        "fear_greed_value": cmc_macro.get("fear_greed_value"),
        "moss_sentiment_today": moss_macro.get("moss_sentiment_today"),
        "moss_sentiment_bias": moss_macro.get("moss_sentiment_bias", "unknown"),
        "altcoin_season_classification": cmc_macro.get("altcoin_season_classification", "unknown"),
        "altcoin_season_value": cmc_macro.get("altcoin_season_value"),
        "market_breadth": cmc_ctx.get("market_breadth", "unknown"),
        "large_cap_leadership": cmc_ctx.get("large_cap_leadership", "unknown"),
        "macro_summary": macro_summary_view["summary"],
        "summary_buckets": macro_summary_view["buckets"],
        "crypto_native_risk_summary": unique_nonempty_strings([event.get("title") for event in crypto_native_summary_events], limit=10),
        "sources": [s for s in ["blockbeats", "cmc", "moss_xsignal", "jin10"] if ctx["health"].get(s) not in {"missing", "error"}],
    })
    ctx["macro"]["geo_risk"] = jin10_data.get("macro", {}).get("geo_risk", "unknown")
    ctx["macro"]["geo_risk_has_shock"] = bool(jin10_data.get("macro", {}).get("geo_risk_has_shock", False))
    ctx["macro"]["event_window"] = bool(jin10_data.get("macro", {}).get("event_window", False))
    ctx["macro"]["event_pre_release"] = bool(jin10_data.get("macro", {}).get("event_pre_release", False))
    ctx["macro"]["event_recent_release"] = bool(jin10_data.get("macro", {}).get("event_recent_release", False))
    ctx["macro"]["regime_bias"] = classify_regime_bias(ctx["macro"], rules.get("macro_regime_rules", {}))
    ctx["macro"]["regime"] = ctx["macro"]["regime_bias"]

    # Phase 2: crypto news is also routed by semantic domains, not by source.
    okx_news = raw_data.get("okx_news", {}).get("data", {})
    opennews = raw_data.get("opennews", {}).get("data", {})
    bb_news = bb.get("crypto_news", {})
    normalized_news_events = [
        event for event in semantic_event_pool
        if any(event_has_domain(event, domain) for domain in {"crypto_native", "flow", "institutional", "regulation", "security"})
        and not (event_has_domain(event, "security") and event.get("source_type") == "macro_summary")
    ]
    ranked_events = sorted(
        normalized_news_events,
        key=lambda item: (item.get("event_score", 0), item.get("holds_match", False), item.get("novelty") == "new"),
        reverse=True,
    )
    next_news_state = update_news_event_state(previous_news_state or {}, ranked_events, now_iso=now_iso)
    security_events = extract_security_events(ranked_events, limit=10)
    derived_news_risk = derive_news_risk(ranked_events, security_events)
    ctx["crypto_news"].update({
        "updated_at": max([x for x in [raw_data.get("okx_news", {}).get("updated_at"), raw_data.get("opennews", {}).get("updated_at"), raw_data.get("blockbeats", {}).get("updated_at")] if x], default=None),
        "market_bias": choose_bias([okx_news.get("market_bias", "unknown"), opennews.get("market_bias", "unknown"), bb_news.get("market_bias", "unknown")]),
        "news_risk": derived_news_risk,
        "high_impact_events": ranked_events[:10],
        "new_high_impact_events": [event for event in ranked_events if event.get("novelty") == "new"][:5],
        "watchlist_events": [event for event in ranked_events if event.get("novelty") != "new"][:5],
        "security_events": security_events,
        "sources": [s for s in ["okx_news", "opennews", "blockbeats"] if ctx["health"].get(s) not in {"missing", "error"}],
    })
    ctx["macro"]["risk_state"] = classify_risk_state({
        "geo_risk": ctx["macro"].get("geo_risk", "unknown"),
        "geo_risk_has_shock": ctx["macro"].get("geo_risk_has_shock", False),
        "event_pre_release": ctx["macro"].get("event_pre_release", False),
        "event_recent_release": ctx["macro"].get("event_recent_release", False),
        "news_risk": ctx["crypto_news"].get("news_risk", "unknown"),
        "security_events": ctx["crypto_news"].get("security_events", []),
        "fear_greed_classification": ctx["macro"].get("fear_greed_classification", "unknown"),
        "moss_sentiment_today": ctx["macro"].get("moss_sentiment_today"),
    })

    # Social combines whitelist Twitter heat with filtered CMC trending candidates and Moss date coverage.
    tw = raw_data.get("opentwitter", {}).get("data", {})
    cmc_social = cmc.get("social", {}) if isinstance(cmc.get("social", {}), dict) else {}
    social_updated_candidates = [
        raw_data.get("opentwitter", {}).get("updated_at"),
        raw_data.get("cmc", {}).get("updated_at"),
        raw_data.get("moss_xsignal", {}).get("updated_at"),
        raw_data.get("okx_market", {}).get("updated_at"),
    ]
    social_sources = [s for s in ["opentwitter", "cmc", "moss_xsignal", "okx_market"] if ctx["health"].get(s) not in {"missing", "error"}]
    okx_market_social = raw_data.get("okx_market", {}).get("data", {}).get("social", {}) if isinstance(raw_data.get("okx_market", {}).get("data", {}).get("social", {}), dict) else {}
    ctx["social"].update({
        "updated_at": max([x for x in social_updated_candidates if x], default=None),
        "market_narrative": tw.get("market_narrative", "unknown"),
        "watch_accounts": tw.get("watch_accounts", []),
        "social_risk": tw.get("social_risk", "unknown"),
        "symbol_mentions": tw.get("symbol_mentions", []),
        "top_discussed_symbols": tw.get("top_discussed_symbols", []),
        "okx_top_gainers": list(okx_market_social.get("okx_top_gainers", []) or []),
        "okx_top_oi": list(okx_market_social.get("okx_top_oi", []) or []),
        "okx_oi_change": list(okx_market_social.get("okx_oi_change", []) or []),
        "okx_gainer_symbols": list(okx_market_social.get("okx_gainer_symbols", []) or []),
        "okx_top_oi_symbols": list(okx_market_social.get("okx_top_oi_symbols", []) or []),
        "okx_oi_change_symbols": list(okx_market_social.get("okx_oi_change_symbols", []) or []),
        "cmc_trending_symbols": list(cmc_social.get("cmc_trending_symbols", []) or []),
        "moss_available_dates": list(moss_social.get("moss_available_dates", []) or []),
        "sources": social_sources,
    })
    ctx["social"].update(build_holdings_focused_social(ctx))

    # Market context from blockbeats + CMC quantitative signals
    bb_ctx = bb.get("market_context", {})
    market_updated_candidates = [
        raw_data.get("blockbeats", {}).get("updated_at"),
        raw_data.get("cmc", {}).get("updated_at"),
    ]
    market_sources = [s for s in ["blockbeats", "cmc"] if ctx["health"].get(s) not in {"missing", "error"}]
    ctx["market_context"].update({
        "updated_at": max([x for x in market_updated_candidates if x], default=None),
        "btc_etf_flow": bb_ctx.get("btc_etf_flow", "unknown"),
        "stablecoin_liquidity": bb_ctx.get("stablecoin_liquidity", "unknown"),
        "onchain_tx_trend": bb_ctx.get("onchain_tx_trend", "unknown"),
        "contract_oi_environment": bb_ctx.get("contract_oi_environment", "unknown"),
        "sentiment_indicator": normalize_sentiment_indicator(bb_ctx.get("sentiment_indicator", "unknown")),
        "fear_greed_classification": cmc_macro.get("fear_greed_classification", "unknown"),
        "fear_greed_value": cmc_macro.get("fear_greed_value"),
        "altcoin_season_classification": cmc_macro.get("altcoin_season_classification", "unknown"),
        "altcoin_season_value": cmc_macro.get("altcoin_season_value"),
        "market_breadth": cmc_ctx.get("market_breadth", "unknown"),
        "large_cap_leadership": cmc_ctx.get("large_cap_leadership", "unknown"),
        "sources": market_sources,
    })

    ctx["macro_context"].update({
        "updated_at": ctx["macro"].get("updated_at"),
        "regime": ctx["macro"].get("regime", "unknown"),
        "regime_bias": ctx["macro"].get("regime_bias", "unknown"),
        "risk_state": ctx["macro"].get("risk_state", "unknown"),
        "geo_risk": ctx["macro"].get("geo_risk", "unknown"),
        "event_window": bool(ctx["macro"].get("event_window")),
        "summary": list(ctx["macro"].get("macro_summary", [])),
        "summary_buckets": dict(ctx["macro"].get("summary_buckets", {})),
    })
    ctx["security"].update({
        "updated_at": ctx["crypto_news"].get("updated_at"),
        "events": list(ctx["crypto_news"].get("security_events", [])),
    })
    ctx["signal_inputs"].update({
        **build_held_symbol_signal_inputs(ctx, semantic_event_pool=semantic_event_pool),
        "us_equity_risk_events": list((ctx["macro_context"].get("summary_buckets", {}) or {}).get("us_equity_sentiment", [])),
        "security_events": list(ctx["security"].get("events", [])),
    })
    ctx["market_state"] = build_market_state(ctx)
    ctx["holdings_state"] = build_holdings_state(ctx)
    ctx["hot_symbols_state"] = build_hot_symbols_state(ctx)

    if return_news_state:
        return ctx, next_news_state
    return ctx


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    load_yaml(SOURCES_FILE)
    rules = load_yaml(RULES_FILE)

    raw_data = {name: load_json(path) for name, path in RAW_FILES.items()}
    previous_news_state = load_news_event_state()
    context, next_news_state = merge_context(raw_data, rules, previous_news_state=previous_news_state, return_news_state=True)
    write_json(FINAL_CACHE_FILE, context)
    write_news_event_state(next_news_state)

    print(json.dumps({
        "ok": True,
        "generated_at": context["generated_at"],
        "context_cache": str(FINAL_CACHE_FILE),
        "news_event_state": str(NEWS_EVENT_STATE_FILE),
        "health": context["health"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
