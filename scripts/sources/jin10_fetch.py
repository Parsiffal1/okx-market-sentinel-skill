#!/usr/bin/env python3
"""Fetch and denoise Jin10 macro/geopolitical data for Phase3."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Sequence

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from _common import get_env, result_error, result_ok, write_raw_cache  # noqa: E402
from semantic_compass import load_semantic_compass  # noqa: E402

SOURCE = "jin10"
RAW_FILENAME = "jin10_cache.json"
JIN10_MCP_URL = "https://mcp.jin10.com/mcp"
RULES_FILE = Path(__file__).resolve().parents[2] / "config" / "phase3_rules.yaml"
DEFAULT_HIGH_GEO_RISK_KEYWORDS = (
    "战争",
    "开战",
    "宣战",
    "空袭",
    "大规模袭击",
    "报复性打击",
    "报复行动",
    "直接参战",
    "地面进攻",
    "地面行动",
    "总动员",
    "无人机袭击",
    "弹道导弹",
    "巡航导弹",
    "霍尔木兹",
    "霍尔木兹海峡",
    "红海",
    "曼德海峡",
    "苏伊士运河",
    "原油运输中断",
    "油轮遇袭",
    "商船遇袭",
    "航运中断",
    "炼油厂遇袭",
    "供应中断",
    "核设施",
    "核设施遇袭",
    "二级制裁",
    "石油禁运",
    "SWIFT制裁",
    "伊朗",
    "以色列",
    "俄罗斯",
    "乌克兰",
)
DEFAULT_MEDIUM_GEO_RISK_KEYWORDS = (
    "停火破裂",
    "停火失败",
    "跨境打击",
    "越境打击",
    "资产冻结",
    "出口管制",
    "航运改道",
    "停航",
    "战争风险保险",
    "保险费飙升",
    "战略石油储备释放",
    "油价飙升",
    "原油暴涨",
    "海上封锁",
    "港口关闭",
    "关税",
    "报复性关税",
)
DEFAULT_EVENT_WINDOW_KEYWORDS = (
    "CPI",
    "核心CPI",
    "PPI",
    "PCE",
    "核心PCE",
    "PMI",
    "ISM",
    "GDP",
    "非农",
    "NFP",
    "失业率",
    "初请失业金",
    "JOLTS",
    "ADP",
    "利率",
    "降息",
    "加息",
    "美联储",
    "鲍威尔",
    "FOMC",
    "点阵图",
    "杰克逊霍尔",
    "关税",
)
DEFAULT_MACRO_SEARCH_KEYWORDS = (
    "特朗普",
    "白宫",
    "美联储",
    "鲍威尔",
    "FOMC",
    "CPI",
    "核心CPI",
    "PCE",
    "核心PCE",
    "非农",
    "NFP",
    "通胀",
    "失业率",
    "利率",
    "原油",
    "霍尔木兹",
    "红海",
    "伊朗",
    "以色列",
    "关税",
    "日本央行",
    "日元",
    "欧佩克",
    "纳斯达克",
    "标普500",
    "SPY",
    "QQQ",
)
DEFAULT_GEO_RISK_SHOCK_KEYWORDS = (
    "海峡关闭",
    "霍尔木兹海峡关闭",
    "关闭霍尔木兹海峡",
    "暂停通行",
    "通行暂停",
    "航运暂停",
    "海上封锁",
    "封锁实施",
    "停火破裂",
    "停火失败",
    "核设施遇袭",
    "开战",
    "宣战",
    "报复性打击",
    "大规模袭击",
    "直接参战",
    "原油运输中断",
    "商船遇袭",
    "油轮遇袭",
    "供应中断",
    "战略石油储备释放",
    "油价飙升",
)
DEFAULT_GEO_RISK_DEESCALATION_KEYWORDS = (
    "尚未达到",
    "未达到",
    "不寻求升级",
    "避免升级",
    "局势降温",
    "保持克制",
    "有限回应",
    "通航自由",
    "保持开放",
    "海峡保持开放",
    "航运未受干扰",
    "未受干扰",
    "未受影响",
    "通行正常",
    "顺利通过",
    "恢复通航",
    "恢复通行",
    "恢复航运",
)
DEFAULT_GEO_RISK_ANCHOR_KEYWORDS = (
    "霍尔木兹",
    "霍尔木兹海峡",
    "红海",
    "曼德海峡",
    "苏伊士运河",
    "伊朗",
    "以色列",
    "美国",
    "美军",
    "胡塞",
    "商船",
    "油轮",
    "航运",
)
IMPORTANT_COUNTRIES = ("美国",)
FetchResult = Dict[str, list[dict[str, Any]]]
FetchFn = Callable[[str], Awaitable[FetchResult]]
WriteCacheFn = Callable[[str, str, str, Dict[str, Any], str | None], Path]


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    parsers = []
    if "T" in value or value.endswith("Z") or "+" in value[10:]:
        parsers.append(lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")))
    parsers.append(lambda v: datetime.strptime(v, "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=8))))
    for parser in parsers:
        try:
            dt = parser(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def normalize_tool_result(result: Any) -> Any:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", None) or []
    for item in content:
        text = getattr(item, "text", None)
        if not text:
            continue
        try:
            return json.loads(text)
        except Exception:
            continue
    return {}


def flatten_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            items = data.get("items")
            if isinstance(items, list):
                return [x for x in items if isinstance(x, dict)]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    return []


def pagination_info(payload: Any) -> tuple[str | None, bool]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            next_cursor = data.get("next_cursor")
            has_more = bool(data.get("has_more"))
            return (str(next_cursor) if next_cursor else None, has_more)
    return (None, False)


def load_macro_rules() -> dict[str, Any]:
    rules = {
        "geo_risk_keywords_high": list(DEFAULT_HIGH_GEO_RISK_KEYWORDS),
        "geo_risk_keywords_medium": list(DEFAULT_MEDIUM_GEO_RISK_KEYWORDS),
        "geo_risk_shock_keywords": list(DEFAULT_GEO_RISK_SHOCK_KEYWORDS),
        "geo_risk_deescalation_keywords": list(DEFAULT_GEO_RISK_DEESCALATION_KEYWORDS),
        "geo_risk_anchor_keywords": list(DEFAULT_GEO_RISK_ANCHOR_KEYWORDS),
        "event_window_crypto_high_relevance_keywords": list(DEFAULT_EVENT_WINDOW_KEYWORDS),
        "list_flash_max_pages": 1,
        "list_news_max_pages": 1,
        "event_window_hours_before": 24,
        "event_window_hours_after": 2,
    }
    if RULES_FILE.exists():
        try:
            import yaml

            payload = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or {}
            macro_rules = payload.get("macro_rules", {}) or {}
            for key in [
                "geo_risk_keywords_high",
                "geo_risk_keywords_medium",
                "geo_risk_shock_keywords",
                "geo_risk_deescalation_keywords",
                "geo_risk_anchor_keywords",
                "event_window_crypto_high_relevance_keywords",
                "macro_summary_relevance_keywords",
                "macro_summary_exclude_keywords",
                "list_flash_max_pages",
                "list_news_max_pages",
                "event_window_hours_before",
                "event_window_hours_after",
            ]:
                value = macro_rules.get(key)
                if value in (None, []):
                    continue
                if key in {
                    "geo_risk_keywords_high",
                    "geo_risk_keywords_medium",
                    "geo_risk_shock_keywords",
                    "geo_risk_deescalation_keywords",
                    "geo_risk_anchor_keywords",
                    "event_window_crypto_high_relevance_keywords",
                    "macro_summary_relevance_keywords",
                    "macro_summary_exclude_keywords",
                } and isinstance(value, list):
                    existing = list(rules.get(key, []))
                    merged: list[Any] = []
                    for item in [*existing, *value]:
                        if item not in merged:
                            merged.append(item)
                    rules[key] = merged
                else:
                    rules[key] = value
        except Exception:
            pass

    compass = load_semantic_compass()
    geo_terms = compass.get('geo_risk', {}) or {}
    mapping = {
        'geo_risk_keywords_high': 'high',
        'geo_risk_keywords_medium': 'medium',
        'geo_risk_shock_keywords': 'shock',
        'geo_risk_deescalation_keywords': 'deescalation',
        'geo_risk_anchor_keywords': 'anchors',
    }
    for rules_key, compass_key in mapping.items():
        existing = list(rules.get(rules_key, []))
        additions = list(geo_terms.get(compass_key, []) or [])
        merged: list[str] = []
        for item in [*existing, *additions]:
            value = str(item or '').strip()
            if value and value not in merged:
                merged.append(value)
        rules[rules_key] = merged
    return rules


def classify_geo_risk_details(texts: Sequence[str], rules: dict[str, Any] | None = None) -> dict[str, Any]:
    rules = rules or load_macro_rules()
    high_keywords = tuple(rules.get("geo_risk_keywords_high", DEFAULT_HIGH_GEO_RISK_KEYWORDS))
    medium_keywords = tuple(rules.get("geo_risk_keywords_medium", DEFAULT_MEDIUM_GEO_RISK_KEYWORDS))
    shock_keywords = tuple(rules.get("geo_risk_shock_keywords", DEFAULT_GEO_RISK_SHOCK_KEYWORDS))
    deescalation_keywords = tuple(rules.get("geo_risk_deescalation_keywords", DEFAULT_GEO_RISK_DEESCALATION_KEYWORDS))
    anchor_keywords = tuple(rules.get("geo_risk_anchor_keywords", DEFAULT_GEO_RISK_ANCHOR_KEYWORDS))
    filtered = [str(t or '').strip() for t in texts if str(t or '').strip()]
    if not filtered:
        return {"level": "unknown", "has_shock": False, "matched_texts": []}

    shock_matches: list[str] = []
    tension_matches: list[str] = []
    calming_matches: list[str] = []
    anchor_only_matches: list[str] = []

    for text in filtered:
        has_anchor = any(keyword in text for keyword in anchor_keywords)
        has_shock = any(keyword in text for keyword in shock_keywords)
        has_high = any(keyword in text for keyword in high_keywords)
        has_medium = any(keyword in text for keyword in medium_keywords)
        has_deescalation = any(keyword in text for keyword in deescalation_keywords)
        if not has_anchor and not (has_high or has_medium or has_shock):
            continue
        if has_deescalation and has_anchor:
            calming_matches.append(text)
            continue
        if has_anchor and has_shock:
            shock_matches.append(text)
            continue
        if has_anchor and (has_high or has_medium):
            tension_matches.append(text)
            continue
        if has_anchor:
            anchor_only_matches.append(text)

    if shock_matches:
        return {"level": "high", "has_shock": True, "matched_texts": shock_matches[:5]}
    if tension_matches:
        return {"level": "medium", "has_shock": False, "matched_texts": tension_matches[:5]}
    if calming_matches or anchor_only_matches:
        return {"level": "low", "has_shock": False, "matched_texts": (calming_matches + anchor_only_matches)[:5]}
    return {"level": "unknown", "has_shock": False, "matched_texts": []}


def classify_geo_risk(texts: Sequence[str], rules: dict[str, Any] | None = None) -> str:
    return classify_geo_risk_details(texts, rules=rules)["level"]


def detect_event_window(calendar_items: Sequence[dict[str, Any]], now: datetime | None = None, rules: dict[str, Any] | None = None) -> dict[str, bool]:
    rules = rules or load_macro_rules()
    current = now or datetime.now(timezone.utc)
    relevance_keywords = tuple(rules.get("event_window_crypto_high_relevance_keywords", DEFAULT_EVENT_WINDOW_KEYWORDS))
    hours_before = float(rules.get("event_window_hours_before", 24))
    hours_after = float(rules.get("event_window_hours_after", 2))
    pre_release = False
    recent_release = False
    for item in calendar_items:
        title = str(item.get("title") or item.get("name") or "")
        country = str(item.get("country") or "")
        importance = int(item.get("importance") or item.get("star") or 0)
        pub_time = parse_dt(str(item.get("time") or item.get("pub_time") or ""))
        if not pub_time:
            continue
        if country and country not in IMPORTANT_COUNTRIES:
            continue
        if importance < 3:
            continue
        if not any(keyword in title for keyword in relevance_keywords):
            continue
        delta_hours = (pub_time - current).total_seconds() / 3600
        if 0 <= delta_hours <= hours_before:
            pre_release = True
        if -hours_after <= delta_hours < 0:
            recent_release = True
        if pre_release and recent_release:
            break
    return {
        "event_window": pre_release or recent_release,
        "event_pre_release": pre_release,
        "event_recent_release": recent_release,
    }


def item_matches_macro_rules(text: str, rules: dict[str, Any] | None = None) -> bool:
    rules = rules or load_macro_rules()
    relevance_keywords = tuple(rules.get("macro_summary_relevance_keywords", []))
    exclude_keywords = tuple(rules.get("macro_summary_exclude_keywords", []))
    if not text:
        return False
    if any(keyword in text for keyword in exclude_keywords):
        return False
    if not relevance_keywords:
        return True
    return any(keyword in text for keyword in relevance_keywords)


def merge_macro_items(
    primary_items: Sequence[dict[str, Any]],
    supplemental_items: Sequence[dict[str, Any]],
    text_getter: Callable[[dict[str, Any]], str],
    rules: dict[str, Any] | None = None,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    rules = rules or load_macro_rules()
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in list(primary_items) + list(supplemental_items):
        text = str(text_getter(item) or "").strip()
        if not item_matches_macro_rules(text, rules=rules):
            continue
        fingerprint = " ".join(text.split())
        if not fingerprint or fingerprint in seen:
            continue
        seen.add(fingerprint)
        merged.append(item)
        if max_items is not None and len(merged) >= max_items:
            break
    return merged


def summarize_items(
    flash_items: Sequence[dict[str, Any]],
    news_items: Sequence[dict[str, Any]],
    rules: dict[str, Any] | None = None,
    limit: int = 5,
) -> list[str]:
    rules = rules or load_macro_rules()

    summary: list[str] = []
    for item in flash_items:
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or "").strip()
        text = " - ".join(part for part in (title, content) if part)
        if item_matches_macro_rules(text, rules=rules):
            summary.append(content[:140] if content else text[:140])
        if len(summary) >= limit:
            return summary
    for item in news_items:
        title = str(item.get("title") or "").strip()
        intro = str(item.get("introduction") or "").strip()
        text = " - ".join(part for part in (title, intro) if part)
        if item_matches_macro_rules(text, rules=rules):
            summary.append(text[:140])
        if len(summary) >= limit:
            return summary
    return summary


def build_macro_payload(
    flash_items: Sequence[dict[str, Any]],
    news_items: Sequence[dict[str, Any]],
    calendar_items: Sequence[dict[str, Any]],
    now: datetime | None = None,
    rules: dict[str, Any] | None = None,
) -> Dict[str, Any]:
    rules = rules or load_macro_rules()
    flash_texts = [str(item.get("content") or "") for item in flash_items]
    news_texts = [
        " - ".join(
            part for part in (str(item.get("title") or "").strip(), str(item.get("introduction") or "").strip()) if part
        )
        for item in news_items
    ]
    flash_risk = classify_geo_risk_details(flash_texts, rules=rules)
    news_risk = classify_geo_risk_details(news_texts, rules=rules)
    order = {"unknown": 0, "low": 1, "medium": 2, "high": 3}
    geo_risk_details = news_risk if order.get(news_risk["level"], 0) >= order.get(flash_risk["level"], 0) else flash_risk
    event_flags = detect_event_window(calendar_items, now=now, rules=rules)
    return {
        "geo_risk": geo_risk_details["level"],
        "geo_risk_has_shock": bool(geo_risk_details.get("has_shock")),
        "geo_risk_matched_texts": list(geo_risk_details.get("matched_texts", [])),
        **event_flags,
        "macro_summary": summarize_items(flash_items, [], rules=rules),
    }


async def fetch_from_mcp(token: str) -> FetchResult:
    headers = {"Authorization": f"Bearer {token}"}
    rules = load_macro_rules()
    list_flash_max_pages = max(1, int(rules.get("list_flash_max_pages", 1)))
    list_news_max_pages = max(1, int(rules.get("list_news_max_pages", 1)))

    async with streamablehttp_client(JIN10_MCP_URL, headers=headers, timeout=30) as streams:
        read_stream, write_stream, _ = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            async def fetch_list_items(tool_name: str, max_pages: int) -> list[dict[str, Any]]:
                items: list[dict[str, Any]] = []
                cursor: str | None = None
                for _ in range(max_pages):
                    params = {"cursor": cursor} if cursor else {}
                    payload = normalize_tool_result(await session.call_tool(tool_name, params))
                    items.extend(flatten_items(payload))
                    cursor, has_more = pagination_info(payload)
                    if not (cursor and has_more):
                        break
                return items

            flash_items = await fetch_list_items("list_flash", list_flash_max_pages)
            news_items = await fetch_list_items("list_news", list_news_max_pages)
            calendar_result = normalize_tool_result(await session.call_tool("list_calendar", {}))
            return {
                "flash_items": merge_macro_items(
                    primary_items=flash_items,
                    supplemental_items=[],
                    text_getter=lambda item: " - ".join(
                        part for part in (str(item.get("title") or "").strip(), str(item.get("content") or "").strip()) if part
                    ),
                    rules=rules,
                ),
                "news_items": merge_macro_items(
                    primary_items=news_items,
                    supplemental_items=[],
                    text_getter=lambda item: " - ".join(
                        part for part in (str(item.get("title") or "").strip(), str(item.get("introduction") or "").strip()) if part
                    ),
                    rules=rules,
                ),
                "calendar_items": flatten_items(calendar_result),
            }


async def run_fetch(
    token: str,
    fetcher: FetchFn = fetch_from_mcp,
    write_cache: WriteCacheFn = write_raw_cache,
    now: datetime | None = None,
) -> Dict[str, Any]:
    if not token:
        raise ValueError("JIN10_MCP_TOKEN is required")

    fetched = await fetcher(token)
    macro_rules = load_macro_rules()
    macro = build_macro_payload(
        flash_items=fetched.get("flash_items", []),
        news_items=fetched.get("news_items", []),
        calendar_items=fetched.get("calendar_items", []),
        now=now,
        rules=macro_rules,
    )
    data = {
        "macro": macro,
        "samples": {
            "flash": fetched.get("flash_items", [])[:10],
            "news": fetched.get("news_items", [])[:10],
            "calendar": fetched.get("calendar_items", [])[:20],
        },
    }
    path = write_cache(RAW_FILENAME, SOURCE, "ok", data)
    return {"status": "ok", "path": path, "data": data}


def main() -> None:
    token = get_env("JIN10_MCP_TOKEN")
    try:
        result = asyncio.run(run_fetch(token=token))
        result_ok(
            result["path"],
            SOURCE,
            {
                "status": result["status"],
                "macro": result["data"]["macro"],
            },
        )
    except Exception as exc:
        path = write_raw_cache(
            RAW_FILENAME,
            SOURCE,
            "error",
            {
                "macro": {
                    "geo_risk": "unknown",
                    "event_window": False,
                    "event_pre_release": False,
                    "event_recent_release": False,
                    "macro_summary": [],
                }
            },
            error=str(exc),
        )
        result_error(SOURCE, f"{exc} (cache written: {path})")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
