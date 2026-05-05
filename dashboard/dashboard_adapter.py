from __future__ import annotations

from typing import Any


def humanize_source_label(source: str) -> str:
    mapping = {
        'holding': '持仓优先',
        'social': '社媒热议',
        'social_hot_list': '社媒热议',
        'cmc': 'CMC趋势',
        'cmc_trending_okx_listed': 'CMC趋势',
        'okx_top_gainers': 'OKX涨幅榜',
        'okx_oi_change': 'OKX持仓异动',
        'okx_oi': 'OKX高持仓',
        'okx_top_oi': 'OKX高持仓',
    }
    return mapping.get(str(source or '').strip(), str(source or '').strip() or '未知来源')


def humanize_reason_label(reason: str) -> str:
    mapping = {
        'existing_holding': '持仓标的',
        'high_social_heat': '社媒高热',
        'multi_account_discussion': '多账户共识',
        'social_symbol_mention': '社媒提及',
        'cmc_trending_symbol': 'CMC趋势上榜',
        'okx_oi_price_up_quadrant': 'OI↑ 价格↑（偏新多）',
        'okx_oi_short_build_quadrant': 'OI↑ 价格↓（偏新空）',
        'okx_oi_short_cover_quadrant': 'OI↓ 价格↑（偏空头回补）',
        'okx_oi_long_exit_quadrant': 'OI↓ 价格↓（偏多头离场）',
        'okx_oi_change_leader': 'OI异动靠前',
        'okx_top_gainer_24h': '24h涨幅靠前',
        'okx_top_oi_contract': '持仓量靠前',
    }
    return mapping.get(str(reason or '').strip(), str(reason or '').strip() or '其他')


def render_source_summary(raw: str | list[str]) -> str:
    if isinstance(raw, str):
        parts = [part.strip() for part in raw.split('+') if part.strip()]
    else:
        parts = [str(part).strip() for part in raw if str(part).strip()]
    labels: list[str] = []
    for part in parts:
        label = humanize_source_label(part)
        if label not in labels:
            labels.append(label)
    return ' + '.join(labels) or '未知来源'


def render_reason_summary(raw: list[str]) -> str:
    labels: list[str] = []
    for part in raw:
        label = humanize_reason_label(part)
        if label not in labels:
            labels.append(label)
    return '；'.join(labels) or '无明确原因'


def detect_asset_class(symbol: str) -> str:
    upper = str(symbol or '').upper().strip()
    us_equities = {'AAPL', 'TSLA', 'QQQ', 'SPY', 'MSTR', 'CRCL', 'COIN', 'NVDA', 'META', 'AMZN', 'MSFT'}
    metals = {'XAU', 'XAG', 'GOLD', 'SILVER', 'GC'}
    commodities = {'CL', 'WTI', 'BRENT', 'NG', 'COPPER'}
    if upper in us_equities:
        return 'us_equity'
    if upper in metals:
        return 'precious_metal'
    if upper in commodities:
        return 'commodity'
    return 'crypto'


def build_health_overview(health: dict[str, Any]) -> str:
    statuses = {str(value or 'unknown').strip().lower() for value in (health or {}).values()}
    if 'error' in statuses or 'stale' in statuses or 'partial' in statuses:
        if 'error' in statuses or 'partial' in statuses:
            return 'partial'
        return 'stale'
    if statuses and statuses <= {'ok'}:
        return 'ok'
    return 'unknown'


def group_quadrants(hot_symbols: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    quadrants = {
        'oi_up_price_up': [],
        'oi_up_price_down': [],
        'oi_down_price_up': [],
        'oi_down_price_down': [],
    }
    for item in hot_symbols:
        reasons = item.get('raw_reasons', []) or []
        if 'okx_oi_price_up_quadrant' in reasons:
            quadrants['oi_up_price_up'].append(item)
        elif 'okx_oi_short_build_quadrant' in reasons:
            quadrants['oi_up_price_down'].append(item)
        elif 'okx_oi_short_cover_quadrant' in reasons:
            quadrants['oi_down_price_up'].append(item)
        elif 'okx_oi_long_exit_quadrant' in reasons:
            quadrants['oi_down_price_down'].append(item)
    return quadrants


def normalize_news(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in events or []:
        title = str(item.get('title') or '').strip()
        if not title:
            continue
        rows.append({
            'title': title,
            'source': str(item.get('source') or 'unknown').strip(),
            'importance': str(item.get('importance') or item.get('impact_level') or item.get('state') or '').strip(),
            'symbols': [str(symbol).strip().upper() for symbol in (item.get('symbols') or []) if str(symbol).strip()],
        })
    return rows


def build_dashboard_payload(context: dict[str, Any], triggers: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    macro = context.get('macro', {}) or {}
    market_state = context.get('market_state', {}) or {}
    health = context.get('health', {}) or {}
    raw_hot = context.get('hot_symbols_state', {}).get('top_tradeable_symbols', []) or []
    hot_symbols: list[dict[str, Any]] = []
    for item in raw_hot:
        symbol = str(item.get('symbol') or '').strip().upper()
        if not symbol:
            continue
        sources = list(item.get('sources') or [])
        reasons = list(item.get('reasons') or [])
        hot_symbols.append({
            'symbol': symbol,
            'score': int(item.get('score', 0) or 0),
            'rank': int(item.get('rank', 0) or 0),
            'asset_class': detect_asset_class(symbol),
            'source_summary': render_source_summary(sources),
            'signal_summary': render_reason_summary(reasons),
            'raw_sources': sources,
            'raw_reasons': reasons,
        })

    payload = {
        'generated_at': context.get('generated_at'),
        'settings': {
            'backend_refresh_minutes': int(settings.get('backend_refresh_minutes', 30) or 30),
            'frontend_poll_seconds': int(settings.get('frontend_poll_seconds', 10) or 10),
            'theme': str(settings.get('theme', 'dark') or 'dark'),
            'compact_mode': bool(settings.get('compact_mode', False)),
            'semantic_compass_focus': str(settings.get('semantic_compass_focus', '') or ''),
            'semantic_compass_last_brief': str(settings.get('semantic_compass_last_brief', '') or ''),
            'semantic_compass_last_updated_at': str(settings.get('semantic_compass_last_updated_at', '') or ''),
            'semantic_compass_refresh_status': str(settings.get('semantic_compass_refresh_status', 'idle') or 'idle'),
        },
        'summary': {
            'regime_bias': str(macro.get('regime_bias') or macro.get('regime') or 'unknown'),
            'risk_state': str(macro.get('risk_state') or 'unknown'),
            'llm_wake_required': bool(triggers.get('llm_wake_required')),
            'event_window': bool(macro.get('event_window')),
            'health_overview': build_health_overview(health),
        },
        'market_state': market_state,
        'holdings_state': context.get('holdings_state', {}) or {},
        'hot_symbols': hot_symbols,
        'quadrants': group_quadrants(hot_symbols),
        'news': {
            'macro_geo': normalize_news([{'title': item, 'source': 'macro_summary'} for item in (macro.get('summary_buckets', {}) or {}).get('geo', [])]),
            'us_equity': normalize_news([{'title': item, 'source': 'macro_summary'} for item in (macro.get('summary_buckets', {}) or {}).get('us_equity_sentiment', [])]),
            'security': normalize_news((context.get('crypto_news', {}) or {}).get('security_events', []) or []),
            'watchlist': normalize_news((context.get('crypto_news', {}) or {}).get('watchlist_events', []) or []),
            'high_impact': normalize_news((context.get('crypto_news', {}) or {}).get('high_impact_events', []) or []),
        },
        'health': health,
        'wake_state': triggers.get('wake_state', {}) or {},
    }
    return payload
