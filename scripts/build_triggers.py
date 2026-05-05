#!/usr/bin/env python3
"""Build trigger candidates from the normalized Phase3 context cache.

This module separates two outcomes:
- wake Hermes/LLM for strict multi-factor risk situations
- rank hot OKX-tradeable instruments for monitoring without waking Hermes
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
CONTEXT_DIR = BASE_DIR / 'context'
CONTEXT_CACHE_FILE = CONTEXT_DIR / 'context_cache.json'
TRIGGER_FILE = CONTEXT_DIR / 'trigger_candidates.json'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_context(path: Path = CONTEXT_CACHE_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def normalize_symbol_mentions(symbol_mentions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in symbol_mentions or []:
        symbol = str(item.get('symbol') or '').upper().strip()
        if symbol:
            result[symbol] = item
    return result


def event_matches_symbol(event: dict[str, Any], symbol: str) -> bool:
    upper_symbol = str(symbol or '').upper().strip()
    if not upper_symbol:
        return False
    event_symbols = {str(item).upper().strip() for item in (event.get('symbols') or []) if str(item).strip()}
    if upper_symbol in event_symbols:
        return True
    for field in ['title', 'summary', 'source']:
        text = str(event.get(field) or '').lower()
        if not text:
            continue
        if re.search(rf'(?<![a-z0-9]){re.escape(upper_symbol.lower())}(?![a-z0-9])', text):
            return True
    return False



def infer_security_state_from_event(event: dict[str, Any]) -> str:
    explicit_state = str(event.get('state') or '').strip()
    if explicit_state:
        return explicit_state
    text = ' '.join([
        str(event.get('title') or ''),
        str(event.get('event_subtype') or ''),
    ]).lower()
    if any(marker in text for marker in ['draining', 'drains funds', 'drain funds', 'live exploit']):
        return 'live_exploit'
    if any(marker in text for marker in ['postmortem', 'patch deployed', 'reimbursement']):
        return 'postmortem'
    if any(marker in text for marker in ['exploit', 'hack', 'breach', 'attacker']):
        return 'post_exploit_active'
    return 'background'



def semantic_security_events(context: dict[str, Any]) -> list[dict[str, Any]]:
    crypto_news = context.get('crypto_news', {}) or {}
    events = list(crypto_news.get('security_events', []) or [])
    for event in crypto_news.get('high_impact_events', []) or []:
        if str(event.get('event_domain') or '').strip().lower() != 'security':
            continue
        state = infer_security_state_from_event(event)
        if state == 'background':
            continue
        events.append({
            'title': str(event.get('title') or ''),
            'source': str(event.get('source') or 'unknown'),
            'state': state,
            'holds_match': bool(event.get('holds_match')),
            'novelty': str(event.get('novelty') or 'unknown'),
            'importance': str(event.get('importance') or event.get('impact_level') or 'unknown'),
        })
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in events:
        key = (str(event.get('title') or ''), str(event.get('source') or ''), str(event.get('state') or ''))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped



def build_semantic_symbol_event_cluster_triggers(context: dict[str, Any]) -> list[dict[str, Any]]:
    holdings = context.get('holdings', {}) or {}
    crypto_news = context.get('crypto_news', {}) or {}
    held_symbols = [str(symbol).upper() for symbol in holdings.get('prioritized_symbols', []) if str(symbol).strip()]
    high_impact_events = crypto_news.get('high_impact_events', []) or []
    triggers: list[dict[str, Any]] = []
    for symbol in held_symbols:
        related_events = [
            event for event in high_impact_events
            if (bool(event.get('holds_match')) or event_matches_symbol(event, symbol))
            and str(event.get('novelty') or '').strip().lower() == 'new'
            and str(event.get('importance') or event.get('impact_level') or '').strip().lower() == 'high'
            and str(event.get('event_domain') or '').strip().lower() in {'security', 'flow', 'institutional', 'regulation', 'crypto_native'}
        ]
        if len(related_events) < 2:
            continue
        triggers.append(
            {
                'scope': 'symbol',
                'symbol': symbol,
                'trigger_type': 'held_symbol_event_cluster',
                'reasons': ['held_symbol_multiple_new_high_importance_events'],
                'priority': 'high',
                'action': 'wake_hermes',
            }
        )
    return triggers


def build_llm_symbol_risk_triggers(context: dict[str, Any]) -> list[dict[str, Any]]:
    holdings = context.get('holdings', {}) or {}
    held_symbols = [str(symbol).upper() for symbol in holdings.get('prioritized_symbols', []) if str(symbol).strip()]
    security_events = semantic_security_events(context)

    triggers: list[dict[str, Any]] = []
    for symbol in held_symbols:
        security_match = next(
            (
                event for event in security_events
                if str(event.get('state') or '').strip().lower() == 'live_exploit' and event_matches_symbol(event, symbol)
            ),
            None,
        )
        if security_match:
            triggers.append(
                {
                    'scope': 'symbol',
                    'symbol': symbol,
                    'trigger_type': 'held_symbol_security_event',
                    'reasons': ['held_symbol_has_live_security_event'],
                    'priority': 'critical',
                    'action': 'wake_hermes',
                }
            )
    return triggers


def build_llm_market_risk_triggers(context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    macro = context.get('macro', {}) or {}
    crypto_news = context.get('crypto_news', {}) or {}
    holdings = context.get('holdings', {}) or {}
    holdings_state = context.get('holdings_state', {}) or {}
    signal_inputs = context.get('signal_inputs', {}) or {}

    reasons: list[str] = []
    regime_bias = str(macro.get('regime_bias') or macro.get('regime') or 'unknown').strip().lower()
    if regime_bias == 'bearish':
        reasons.append('bearish_regime')
    if macro.get('geo_risk') == 'high':
        reasons.append('geo_risk_high')
    if bool(macro.get('event_window')):
        reasons.append('event_window_active')
    if crypto_news.get('news_risk') == 'high':
        reasons.append('crypto_news_risk_high')

    observe_only_triggers: list[dict[str, Any]] = []
    high_impact_events = crypto_news.get('high_impact_events', []) or []
    if any(
        str(event.get('event_subtype') or '').strip().lower() == 'us_equity_risk_sentiment'
        and str(event.get('importance') or event.get('impact_level') or '').strip().lower() == 'high'
        for event in high_impact_events
    ):
        observe_only_triggers.append(
            {
                'scope': 'market',
                'symbol': None,
                'trigger_type': 'us_equity_risk_proxy_shift',
                'reasons': ['us_equity_risk_off_proxy'],
                'priority': 'medium',
                'action': 'observe_only',
            }
        )

    if len(reasons) < 4:
        return [], observe_only_triggers

    has_positions = bool(holdings.get('has_positions'))
    held_symbols = {
        str(symbol).upper().strip()
        for symbol in (holdings.get('prioritized_symbols', []) or [])
        if str(symbol).strip()
    }
    raw_symbol_risk_rows = holdings_state.get('symbol_risk', []) or []
    symbol_risk_rows = [
        item for item in raw_symbol_risk_rows
        if not held_symbols or str(item.get('symbol') or '').upper().strip() in held_symbols
    ]
    held_symbol_risk_events = signal_inputs.get('held_symbol_risk_events', []) or []
    held_symbol_social_heat = signal_inputs.get('held_symbol_social_heat', []) or []
    holdings_at_risk = any(str(item.get('risk_state') or '').strip().lower() in {'high', 'extreme'} for item in symbol_risk_rows)
    if not holdings_at_risk and len(held_symbol_risk_events) >= 2:
        holdings_at_risk = True
    if not holdings_at_risk and any(int(item.get('weighted_heat', 0) or 0) >= 80000 for item in held_symbol_social_heat):
        holdings_at_risk = True

    if not has_positions:
        observe_only_triggers.append(
            {
                'scope': 'market',
                'symbol': None,
                'trigger_type': 'macro_risk_confluence',
                'reasons': list(reasons) + ['no_positions_to_defend'],
                'priority': 'high',
                'action': 'observe_only',
            }
        )
        return [], observe_only_triggers

    if not holdings_at_risk:
        observe_only_triggers.append(
            {
                'scope': 'market',
                'symbol': None,
                'trigger_type': 'macro_risk_confluence',
                'reasons': list(reasons) + ['positions_not_yet_at_risk'],
                'priority': 'high',
                'action': 'observe_only',
            }
        )
        return [], observe_only_triggers

    return [
        {
            'scope': 'market',
            'symbol': None,
            'trigger_type': 'macro_risk_confluence',
            'reasons': list(reasons) + ['held_positions_at_risk'],
            'priority': 'high',
            'action': 'wake_hermes',
        }
    ], observe_only_triggers


def build_hot_symbols_ranking(context: dict[str, Any]) -> list[dict[str, Any]]:
    hot_symbols_state = context.get('hot_symbols_state', {}) or {}
    hot_symbols = hot_symbols_state.get('top_tradeable_symbols', []) or []
    if hot_symbols:
        prioritized: list[dict[str, Any]] = []
        seen_symbols: set[str] = set()
        for item in hot_symbols:
            symbol = str(item.get('symbol') or '').strip().upper()
            if not symbol or symbol in seen_symbols:
                continue
            raw_sources = [str(source).strip() for source in (item.get('sources') or []) if str(source).strip()]
            reasons = [str(reason).strip() for reason in (item.get('reasons') or []) if str(reason).strip()]
            if 'holding' in raw_sources:
                priority = 'critical'
            elif 'social' in raw_sources:
                priority = 'high'
            elif 'okx_top_gainers' in raw_sources or 'okx_top_oi' in raw_sources or 'okx_oi_change' in raw_sources:
                priority = 'medium'
            elif 'cmc' in raw_sources:
                priority = 'medium'
            else:
                priority = 'medium'

            if raw_sources == ['holding']:
                source = 'holding'
            elif raw_sources == ['social']:
                source = 'social_hot_list'
            elif raw_sources == ['cmc']:
                source = 'cmc_trending_okx_listed'
            elif raw_sources == ['okx_top_gainers']:
                source = 'okx_top_gainers'
            elif raw_sources == ['okx_top_oi']:
                source = 'okx_oi'
            elif raw_sources == ['okx_oi_change']:
                source = 'okx_oi_change'
            else:
                mapped_sources = []
                for raw_source in raw_sources:
                    if raw_source == 'social':
                        mapped_sources.append('social')
                    elif raw_source == 'cmc':
                        mapped_sources.append('cmc')
                    elif raw_source == 'holding':
                        mapped_sources.append('holding')
                    else:
                        mapped_sources.append(raw_source)
                source = '+'.join(mapped_sources) or 'derived_hot_symbols'

            prioritized.append(
                {
                    'symbol': symbol,
                    'source': source,
                    'priority': priority,
                    'reasons': reasons or ['derived_from_hot_symbols_state'],
                }
            )
            seen_symbols.add(symbol)
        return prioritized

    social = context.get('social', {}) or {}
    holdings = context.get('holdings', {}) or {}
    symbol_mentions = normalize_symbol_mentions(social.get('symbol_mentions', []))
    prioritized: list[dict[str, Any]] = []
    seen_symbols: set[str] = set()

    for symbol in holdings.get('prioritized_symbols', []) or []:
        upper_symbol = str(symbol).upper().strip()
        if not upper_symbol or upper_symbol in seen_symbols:
            continue
        prioritized.append(
            {
                'symbol': upper_symbol,
                'source': 'holding',
                'priority': 'critical',
                'reasons': ['existing_holding'],
            }
        )
        seen_symbols.add(upper_symbol)

    for symbol in social.get('top_discussed_symbols', []) or []:
        upper_symbol = str(symbol).upper().strip()
        if not upper_symbol or upper_symbol in seen_symbols:
            continue
        mention = symbol_mentions.get(upper_symbol, {})
        if int(mention.get('weighted_heat', 0) or 0) < 80000:
            continue
        if int(mention.get('unique_accounts', 0) or 0) < 2:
            continue
        prioritized.append(
            {
                'symbol': upper_symbol,
                'source': 'social_hot_list',
                'priority': 'high',
                'reasons': ['high_social_heat', 'multi_account_discussion'],
            }
        )
        seen_symbols.add(upper_symbol)

    for symbol in social.get('cmc_trending_symbols', []) or []:
        upper_symbol = str(symbol).upper().strip()
        if not upper_symbol or upper_symbol in seen_symbols:
            continue
        prioritized.append(
            {
                'symbol': upper_symbol,
                'source': 'cmc_trending_okx_listed',
                'priority': 'medium',
                'reasons': ['cmc_trending_symbol', 'okx_tradable_contract'],
            }
        )
        seen_symbols.add(upper_symbol)

    for item in social.get('okx_top_gainers', []) or []:
        upper_symbol = str(item.get('symbol') or '').upper().strip()
        if not upper_symbol or upper_symbol in seen_symbols:
            continue
        prioritized.append(
            {
                'symbol': upper_symbol,
                'source': 'okx_top_gainers',
                'priority': 'medium',
                'reasons': ['okx_top_gainer_24h'],
            }
        )
        seen_symbols.add(upper_symbol)

    for item in social.get('okx_oi_change', []) or []:
        upper_symbol = str(item.get('symbol') or '').upper().strip()
        if not upper_symbol or upper_symbol in seen_symbols:
            continue
        quadrant = str(item.get('quadrant') or '').strip()
        quadrant_reason = {
            'oi_up_price_up': 'okx_oi_price_up_quadrant',
            'oi_up_price_down': 'okx_oi_short_build_quadrant',
            'oi_down_price_up': 'okx_oi_short_cover_quadrant',
            'oi_down_price_down': 'okx_oi_long_exit_quadrant',
        }.get(quadrant, 'okx_oi_change_leader')
        prioritized.append(
            {
                'symbol': upper_symbol,
                'source': 'okx_oi_change',
                'priority': 'medium',
                'reasons': [quadrant_reason, 'okx_oi_change_leader'],
            }
        )
        seen_symbols.add(upper_symbol)
    return prioritized


def build_wake_state(
    llm_wake_required: bool,
    llm_wake_triggers: list[dict[str, Any]],
    observe_only_triggers: list[dict[str, Any]],
) -> dict[str, Any]:
    priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
    wake_priority = 'none'
    if llm_wake_triggers:
        wake_priority = max(
            (str(item.get('priority') or 'low').strip().lower() for item in llm_wake_triggers),
            key=lambda value: priority_order.get(value, -1),
        )
    return {
        'llm_wake_required': llm_wake_required,
        'wake_priority': wake_priority,
        'wake_reasons': [str(item.get('trigger_type') or 'unknown') for item in llm_wake_triggers],
        'observe_only_reasons': [str(item.get('trigger_type') or 'unknown') for item in observe_only_triggers],
    }


def build_triggers(context: dict[str, Any]) -> dict[str, Any]:
    symbol_wake_triggers = build_llm_symbol_risk_triggers(context)
    cluster_wake_triggers = build_semantic_symbol_event_cluster_triggers(context)
    market_wake_triggers, observe_only_triggers = build_llm_market_risk_triggers(context)
    llm_wake_triggers = symbol_wake_triggers + [
        trigger for trigger in cluster_wake_triggers
        if trigger not in symbol_wake_triggers
    ] + market_wake_triggers
    hot_symbols_ranking = build_hot_symbols_ranking(context)
    llm_wake_required = bool(llm_wake_triggers)
    return {
        'generated_at': utc_now(),
        'schema_version': 1,
        'llm_wake_required': llm_wake_required,
        'llm_wake_triggers': llm_wake_triggers,
        'observe_only_triggers': observe_only_triggers,
        'hot_symbols_ranking': hot_symbols_ranking,
        'wake_state': build_wake_state(llm_wake_required, llm_wake_triggers, observe_only_triggers),
    }


def main() -> None:
    context = load_context()
    triggers = build_triggers(context)
    TRIGGER_FILE.write_text(json.dumps(triggers, ensure_ascii=False, indent=2), encoding='utf-8')
    payload = {
        'ok': True,
        'trigger_file': str(TRIGGER_FILE),
        'llm_wake_required': triggers['llm_wake_required'],
        'llm_wake_triggers': len(triggers['llm_wake_triggers']),
        'observe_only_triggers': len(triggers['observe_only_triggers']),
        'hot_symbols_ranking': len(triggers['hot_symbols_ranking']),
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main()
