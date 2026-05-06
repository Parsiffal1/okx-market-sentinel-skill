from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "dashboard/dashboard_adapter.py"
MODULE_DIR = MODULE_PATH.parent


def load_module():
    if str(MODULE_DIR) not in sys.path:
        sys.path.insert(0, str(MODULE_DIR))
    spec = importlib.util.spec_from_file_location('dashboard_adapter_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sample_context() -> dict:
    return {
        'generated_at': '2026-05-05T12:00:00+00:00',
        'macro': {
            'updated_at': '2026-05-05T11:59:00+00:00',
            'regime_bias': 'neutral',
            'risk_state': 'high',
            'geo_risk': 'medium',
            'event_window': True,
            'summary_buckets': {
                'geo': ['霍尔木兹海峡紧张局势升级'],
                'macro_financial': ['美元指数走强'],
                'us_equity_sentiment': ['COIN盘前大涨'],
            },
            'crypto_native_risk_summary': ['交易所安全风险仍需观察'],
        },
        'market_state': {
            'market_sentiment': 'neutral',
            'sentiment_confidence': 0.88,
            'risk_state': 'high',
            'geo_risk': 'medium',
            'event_window': True,
            'macro_drivers': ['霍尔木兹海峡紧张局势升级'],
            'crypto_native_risk_drivers': ['交易所安全风险仍需观察'],
            'summary': ['宏观偏谨慎'],
        },
        'holdings_state': {
            'has_positions': True,
            'prioritized_symbols': ['BTC', 'AAPL'],
            'symbol_risk': [
                {'symbol': 'BTC', 'risk_state': 'high', 'relevant_event_count': 2, 'relevant_social_heat': 92000, 'reasons': ['held_symbol_event_cluster']},
            ],
        },
        'hot_symbols_state': {
            'updated_at': '2026-05-05T11:59:30+00:00',
            'top_tradeable_symbols': [
                {'symbol': 'TON', 'score': 65, 'rank': 1, 'sources': ['cmc', 'okx_oi_change', 'okx_top_gainers'], 'reasons': ['cmc_trending_symbol', 'okx_oi_price_up_quadrant', 'okx_top_gainer_24h']},
                {'symbol': 'AAPL', 'score': 33, 'rank': 2, 'sources': ['okx_top_gainers', 'okx_top_oi'], 'reasons': ['okx_top_gainer_24h', 'okx_top_oi_contract']},
            ],
        },
        'crypto_news': {
            'high_impact_events': [
                {'title': 'Strategy将于明日召开财报电话会议', 'source': 'blockbeats', 'importance': 'high'},
            ],
            'watchlist_events': [
                {'title': 'TON生态热度持续升温', 'source': 'okx_news', 'importance': 'high'},
            ],
            'security_events': [
                {'title': 'Bridge exploit drains funds', 'source': 'okx_news', 'state': 'live_exploit'},
            ],
        },
        'health': {
            'okx_market': 'ok',
            'okx_positions': 'ok',
            'blockbeats': 'ok',
            'cmc': 'ok',
            'opennews': 'partial',
        },
    }


def sample_triggers() -> dict:
    return {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [{'trigger_type': 'macro_risk_confluence'}],
        'hot_symbols_ranking': [
            {'symbol': 'TON', 'source': 'cmc+okx_oi_change+okx_top_gainers', 'priority': 'medium', 'reasons': ['cmc_trending_symbol', 'okx_oi_price_up_quadrant', 'okx_top_gainer_24h']},
            {'symbol': 'AAPL', 'source': 'okx_top_gainers+okx_oi', 'priority': 'medium', 'reasons': ['okx_top_gainer_24h', 'okx_top_oi_contract']},
        ],
        'wake_state': {
            'llm_wake_required': False,
            'wake_priority': 'none',
            'wake_reasons': [],
            'observe_only_reasons': ['macro_risk_confluence'],
        },
    }


def test_build_dashboard_payload_returns_summary_hot_symbols_and_quadrants():
    mod = load_module()
    payload = mod.build_dashboard_payload(sample_context(), sample_triggers(), {'backend_refresh_minutes': 30, 'frontend_poll_seconds': 10})

    assert payload['summary'] == {
        'regime_bias': 'neutral',
        'risk_state': 'high',
        'llm_wake_required': False,
        'event_window': True,
        'health_overview': 'partial',
    }
    assert payload['settings']['backend_refresh_minutes'] == 30
    assert payload['settings']['frontend_poll_seconds'] == 10
    assert payload['hot_symbols'][0]['symbol'] == 'TON'
    assert payload['hot_symbols'][0]['asset_class'] == 'crypto'
    assert payload['hot_symbols'][0]['source_summary'] == 'CMC趋势 + OKX持仓异动 + OKX涨幅榜'
    assert payload['hot_symbols'][0]['signal_summary'] == 'CMC趋势上榜；OI↑ 价格↑（偏新多）；24h涨幅靠前'
    assert payload['hot_symbols'][1]['asset_class'] == 'us_equity'
    assert payload['quadrants']['oi_up_price_up'][0]['symbol'] == 'TON'
    assert payload['news']['security'][0]['source'] == 'okx_news'
    assert payload['hot_symbols_meta']['asset_class_counts']['crypto'] == 1
    assert payload['hot_symbols_meta']['asset_class_counts']['us_equity'] == 1
    assert payload['hot_symbols_meta']['source_counts']['CMC趋势'] == 1
    assert payload['hot_symbols_meta']['source_counts']['OKX持仓异动'] == 1
    assert payload['quadrant_counts']['oi_up_price_up'] == 1
    assert payload['news_counts']['high_impact'] == 1
    assert payload['holdings_meta']['has_positions'] is True
    assert payload['holdings_meta']['held_symbol_count'] == 2
    assert payload['holdings_meta']['highest_risk_state'] == 'high'


def test_humanize_source_and_reason_labels_are_user_readable():
    mod = load_module()
    assert mod.humanize_source_label('okx_top_oi') == 'OKX高持仓'
    assert mod.humanize_source_label('social') == '社媒热议'
    assert mod.humanize_reason_label('okx_oi_short_build_quadrant') == 'OI↑ 价格↓（偏新空）'
    assert mod.humanize_reason_label('existing_holding') == '持仓标的'
