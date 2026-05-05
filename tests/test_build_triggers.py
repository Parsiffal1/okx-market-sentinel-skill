from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/build_triggers.py"
SCRIPTS_DIR = MODULE_PATH.parent


def load_module():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location('build_triggers_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sample_context() -> dict:
    return {
        'generated_at': '2026-04-23T09:40:35+00:00',
        'macro': {
            'regime': 'bearish',
            'regime_bias': 'bearish',
            'risk_state': 'high',
            'geo_risk': 'high',
            'event_window': True,
            'event_pre_release': True,
            'event_recent_release': False,
            'crypto_native_risk_summary': ['Exchange issue remains under monitoring'],
        },
        'crypto_news': {
            'news_risk': 'high',
            'high_impact_events': [
                {'title': 'Strategy buys more BTC', 'impact': 'bullish', 'source': 'okx_news'},
                {'title': 'RAVE launches major protocol update', 'impact': 'neutral', 'source': 'okx_news'},
            ],
            'security_events': [],
        },
        'holdings': {
            'has_positions': True,
            'prioritized_symbols': ['BTC', 'RAVE'],
            'live_symbols': [],
            'demo_symbols': ['BTC', 'RAVE'],
        },
        'holdings_state': {
            'has_positions': True,
            'prioritized_symbols': ['BTC', 'RAVE'],
            'symbol_risk': [
                {
                    'symbol': 'BTC',
                    'risk_state': 'high',
                    'relevant_event_count': 2,
                    'relevant_social_heat': 195665,
                    'macro_alignment': 'bearish',
                    'reasons': ['held_symbol_event_cluster', 'held_symbol_social_heat_elevated'],
                },
                {
                    'symbol': 'RAVE',
                    'risk_state': 'medium',
                    'relevant_event_count': 1,
                    'relevant_social_heat': 43418,
                    'macro_alignment': 'bearish',
                    'reasons': ['global_market_risk_medium'],
                },
            ],
        },
        'signal_inputs': {
            'held_symbol_risk_events': [
                {'title': 'BTC funding squeeze risk rises', 'source': 'okx_news', 'symbols': ['BTC']},
                {'title': 'RAVE ecosystem treasury update draws attention', 'source': 'okx_news', 'symbols': ['RAVE']},
            ],
            'held_symbol_social_heat': [
                {'symbol': 'BTC', 'mention_count': 11, 'unique_accounts': 5, 'weighted_heat': 195665},
                {'symbol': 'RAVE', 'mention_count': 1, 'unique_accounts': 1, 'weighted_heat': 43418},
            ],
        },
        'social': {
            'top_discussed_symbols': ['BTC', 'ETH', 'RAVE'],
            'cmc_trending_symbols': [],
            'symbol_mentions': [
                {'symbol': 'BTC', 'mention_count': 11, 'unique_accounts': 5, 'weighted_heat': 195665},
                {'symbol': 'ETH', 'mention_count': 7, 'unique_accounts': 4, 'weighted_heat': 120597},
                {'symbol': 'RAVE', 'mention_count': 1, 'unique_accounts': 1, 'weighted_heat': 43418},
            ],
        },
        'market_context': {
            'btc_etf_flow': 'positive',
            'stablecoin_liquidity': 'contracting',
            'onchain_tx_trend': 'positive',
            'contract_oi_environment': 'positive',
            'sentiment_indicator': 'neutral',
        },
        'hot_symbols_state': {
            'updated_at': '2026-04-23T09:40:35+00:00',
            'top_tradeable_symbols': [
                {'symbol': 'BTC', 'score': 120, 'rank': 1, 'sources': ['holding'], 'reasons': ['existing_holding']},
                {'symbol': 'ETH', 'score': 86, 'rank': 2, 'sources': ['social'], 'reasons': ['high_social_heat', 'multi_account_discussion']},
                {'symbol': 'RAVE', 'score': 68, 'rank': 3, 'sources': ['holding', 'cmc'], 'reasons': ['existing_holding', 'cmc_trending_symbol']},
            ],
        },
        'health': {
            'jin10': 'ok',
            'blockbeats': 'ok',
            'okx_positions': 'ok',
            'okx_news': 'ok',
            'opennews': 'ok',
            'opentwitter': 'ok',
        },
    }


def test_build_triggers_wakes_llm_for_macro_confluence_when_holdings_are_at_risk():
    mod = load_module()
    context = sample_context()

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is True
    assert triggers['llm_wake_triggers'] == [
        {
            'scope': 'market',
            'symbol': None,
            'trigger_type': 'macro_risk_confluence',
            'reasons': ['bearish_regime', 'geo_risk_high', 'event_window_active', 'crypto_news_risk_high', 'held_positions_at_risk'],
            'priority': 'high',
            'action': 'wake_hermes',
        }
    ]
    assert triggers['observe_only_triggers'] == []
    assert triggers['wake_state'] == {
        'llm_wake_required': True,
        'wake_priority': 'high',
        'wake_reasons': ['macro_risk_confluence'],
        'observe_only_reasons': [],
    }
    assert triggers['hot_symbols_ranking'] == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'source': 'social_hot_list',
            'priority': 'high',
            'reasons': ['high_social_heat', 'multi_account_discussion'],
        },
        {
            'symbol': 'RAVE',
            'source': 'holding+cmc',
            'priority': 'critical',
            'reasons': ['existing_holding', 'cmc_trending_symbol'],
        },
    ]
    assert set(triggers) == {'generated_at', 'schema_version', 'llm_wake_required', 'llm_wake_triggers', 'observe_only_triggers', 'hot_symbols_ranking', 'wake_state'}


def test_build_triggers_keeps_macro_confluence_reason_set_simple_even_with_crypto_native_escalation_present():
    mod = load_module()
    context = sample_context()
    context['macro']['crypto_native_risk_summary'] = ['Major exchange exploit escalates and contagion risk rises']

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is True
    assert triggers['llm_wake_triggers'] == [
        {
            'scope': 'market',
            'symbol': None,
            'trigger_type': 'macro_risk_confluence',
            'reasons': ['bearish_regime', 'geo_risk_high', 'event_window_active', 'crypto_news_risk_high', 'held_positions_at_risk'],
            'priority': 'high',
            'action': 'wake_hermes',
        }
    ]
    assert triggers['observe_only_triggers'] == []



def test_build_triggers_downgrades_macro_confluence_to_observe_only_when_no_positions_exist():
    mod = load_module()
    context = sample_context()
    context['holdings'] = {'has_positions': False, 'prioritized_symbols': [], 'live_symbols': [], 'demo_symbols': []}
    context['holdings_state'] = {'has_positions': False, 'prioritized_symbols': [], 'symbol_risk': []}
    context['signal_inputs'] = {'held_symbol_risk_events': [], 'held_symbol_social_heat': []}

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is False
    assert triggers['llm_wake_triggers'] == []
    assert triggers['observe_only_triggers'] == [
        {
            'scope': 'market',
            'symbol': None,
            'trigger_type': 'macro_risk_confluence',
            'reasons': ['bearish_regime', 'geo_risk_high', 'event_window_active', 'crypto_news_risk_high', 'no_positions_to_defend'],
            'priority': 'high',
            'action': 'observe_only',
        }
    ]
    assert triggers['wake_state'] == {
        'llm_wake_required': False,
        'wake_priority': 'none',
        'wake_reasons': [],
        'observe_only_reasons': ['macro_risk_confluence'],
    }


def test_build_triggers_downgrades_macro_confluence_to_observe_only_when_positions_exist_but_are_not_yet_at_risk():
    mod = load_module()
    context = sample_context()
    context['holdings_state'] = {
        'has_positions': True,
        'prioritized_symbols': ['BTC', 'RAVE'],
        'symbol_risk': [
            {'symbol': 'BTC', 'risk_state': 'medium', 'relevant_event_count': 1, 'relevant_social_heat': 30000, 'macro_alignment': 'bearish', 'reasons': ['global_market_risk_medium']},
            {'symbol': 'RAVE', 'risk_state': 'low', 'relevant_event_count': 0, 'relevant_social_heat': 12000, 'macro_alignment': 'bearish', 'reasons': ['global_market_risk_low']},
        ],
    }
    context['signal_inputs'] = {'held_symbol_risk_events': [{'title': 'BTC funding squeeze risk rises', 'source': 'okx_news', 'symbols': ['BTC']}], 'held_symbol_social_heat': []}

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is False
    assert triggers['llm_wake_triggers'] == []
    assert triggers['observe_only_triggers'] == [
        {
            'scope': 'market',
            'symbol': None,
            'trigger_type': 'macro_risk_confluence',
            'reasons': ['bearish_regime', 'geo_risk_high', 'event_window_active', 'crypto_news_risk_high', 'positions_not_yet_at_risk'],
            'priority': 'high',
            'action': 'observe_only',
        }
    ]



def test_build_triggers_does_not_wake_llm_for_postmortem_security_followup_event():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'
    context['crypto_news']['security_events'] = [
        {'title': 'KelpDAO黑客完成洗币，近2000枚BTC转出', 'source': 'blockbeats', 'state': 'postmortem'},
    ]

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is False
    assert triggers['llm_wake_triggers'] == []
    assert triggers['observe_only_triggers'] == []


def test_build_triggers_does_not_wake_llm_for_btc_news_plus_social_only():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['regime_bias'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is False
    assert triggers['llm_wake_triggers'] == []
    assert triggers['observe_only_triggers'] == []
    assert triggers['hot_symbols_ranking'] == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'source': 'social_hot_list',
            'priority': 'high',
            'reasons': ['high_social_heat', 'multi_account_discussion'],
        },
        {
            'symbol': 'RAVE',
            'source': 'holding+cmc',
            'priority': 'critical',
            'reasons': ['existing_holding', 'cmc_trending_symbol'],
        },
    ]



def test_build_triggers_uses_semantic_security_event_even_when_security_summary_is_missing():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'
    context['crypto_news']['security_events'] = []
    context['crypto_news']['high_impact_events'] = [
        {
            'title': 'RAVE bridge exploit drains funds from treasury',
            'source': 'okx_news',
            'event_domain': 'security',
            'event_subtype': 'exploit',
            'importance': 'high',
            'holds_match': True,
            'novelty': 'new',
        }
    ]

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is True
    assert triggers['llm_wake_triggers'] == [
        {
            'scope': 'symbol',
            'symbol': 'RAVE',
            'trigger_type': 'held_symbol_security_event',
            'reasons': ['held_symbol_has_live_security_event'],
            'priority': 'critical',
            'action': 'wake_hermes',
        }
    ]



def test_build_triggers_adds_observe_only_trigger_for_us_equity_risk_off_proxy_shift():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'
    context['crypto_news']['high_impact_events'] = [
        {
            'title': '纳斯达克指数盘初跌超1.5%，QQQ与SPY同步走弱，风险资产承压',
            'source': 'jin10',
            'event_domain': 'geo',
            'event_subtype': 'us_equity_risk_sentiment',
            'importance': 'high',
            'holds_match': False,
            'novelty': 'new',
        }
    ]

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is False
    assert {'scope': 'market', 'symbol': None, 'trigger_type': 'us_equity_risk_proxy_shift', 'reasons': ['us_equity_risk_off_proxy'], 'priority': 'medium', 'action': 'observe_only'} in triggers['observe_only_triggers']



def test_event_matches_symbol_uses_token_aware_matching_for_short_tickers():
    mod = load_module()

    assert mod.event_matches_symbol({'title': 'ETH whale buys spot during breakout'}, 'ETH') is True
    assert mod.event_matches_symbol({'title': 'Tether freezes suspicious address'}, 'ETH') is False
    assert mod.event_matches_symbol({'title': 'SOL ecosystem sees stable inflows'}, 'SOL') is True
    assert mod.event_matches_symbol({'title': 'Consolidation continues after CPI release'}, 'SOL') is False



def test_build_triggers_wakes_llm_for_held_symbol_semantic_event_cluster():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'
    context['crypto_news']['high_impact_events'] = [
        {
            'title': 'RAVE bridge exploit drains funds from treasury',
            'source': 'okx_news',
            'event_domain': 'security',
            'event_subtype': 'exploit',
            'importance': 'high',
            'holds_match': True,
            'novelty': 'new',
        },
        {
            'title': 'RAVE whale deposits tokens to exchange after exploit',
            'source': 'blockbeats',
            'event_domain': 'flow',
            'event_subtype': 'exchange_inflow',
            'importance': 'high',
            'holds_match': True,
            'novelty': 'new',
        },
    ]

    triggers = mod.build_triggers(context)

    assert any(item['trigger_type'] == 'held_symbol_event_cluster' for item in triggers['llm_wake_triggers'])
    assert triggers['llm_wake_required'] is True
    assert {
        'scope': 'symbol',
        'symbol': 'RAVE',
        'trigger_type': 'held_symbol_event_cluster',
        'reasons': ['held_symbol_multiple_new_high_importance_events'],
        'priority': 'high',
        'action': 'wake_hermes',
    } in triggers['llm_wake_triggers']


def test_build_hot_symbols_ranking_falls_back_to_legacy_sources_when_hot_symbols_state_missing():
    mod = load_module()
    context = sample_context()
    context['hot_symbols_state'] = {'updated_at': None, 'top_tradeable_symbols': []}
    context['social']['cmc_trending_symbols'] = ['SOL']
    context['social']['okx_top_gainers'] = [{'symbol': 'AAPL'}]
    context['social']['okx_gainer_symbols'] = ['AAPL']
    context['social']['okx_top_oi'] = [{'symbol': 'ETH'}]
    context['social']['okx_top_oi_symbols'] = ['ETH']
    context['social']['okx_oi_change'] = [{'symbol': 'GC', 'quadrant': 'oi_up_price_up'}]
    context['social']['okx_oi_change_symbols'] = ['GC']

    priority = mod.build_hot_symbols_ranking(context)

    assert priority == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'RAVE',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'source': 'social_hot_list',
            'priority': 'high',
            'reasons': ['high_social_heat', 'multi_account_discussion'],
        },
        {
            'symbol': 'SOL',
            'source': 'cmc_trending_okx_listed',
            'priority': 'medium',
            'reasons': ['cmc_trending_symbol', 'okx_tradable_contract'],
        },
        {
            'symbol': 'AAPL',
            'source': 'okx_top_gainers',
            'priority': 'medium',
            'reasons': ['okx_top_gainer_24h'],
        },
        {
            'symbol': 'GC',
            'source': 'okx_oi_change',
            'priority': 'medium',
            'reasons': ['okx_oi_price_up_quadrant', 'okx_oi_change_leader'],
        },
    ]



def test_build_hot_symbols_ranking_prefers_hot_symbols_state_order_and_semantics():
    mod = load_module()
    context = sample_context()
    context['social']['cmc_trending_symbols'] = ['RAVE']

    priority = mod.build_hot_symbols_ranking(context)

    assert priority == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'source': 'social_hot_list',
            'priority': 'high',
            'reasons': ['high_social_heat', 'multi_account_discussion'],
        },
        {
            'symbol': 'RAVE',
            'source': 'holding+cmc',
            'priority': 'critical',
            'reasons': ['existing_holding', 'cmc_trending_symbol'],
        },
    ]



def test_build_hot_symbols_ranking_dedupes_duplicate_hot_symbol_entries():
    mod = load_module()
    context = sample_context()
    context['hot_symbols_state']['top_tradeable_symbols'] = [
        {'symbol': 'BTC', 'score': 120, 'rank': 1, 'sources': ['holding'], 'reasons': ['existing_holding']},
        {'symbol': 'BTC', 'score': 99, 'rank': 2, 'sources': ['social'], 'reasons': ['high_social_heat']},
        {'symbol': 'ETH', 'score': 86, 'rank': 3, 'sources': ['social'], 'reasons': ['high_social_heat', 'multi_account_discussion']},
    ]

    priority = mod.build_hot_symbols_ranking(context)

    assert priority == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'source': 'social_hot_list',
            'priority': 'high',
            'reasons': ['high_social_heat', 'multi_account_discussion'],
        },
    ]



def test_build_triggers_can_add_okx_filtered_cmc_trending_symbol_but_keeps_twitter_symbols_higher_priority():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['regime_bias'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'
    context['social']['cmc_trending_symbols'] = ['SOL']
    context['hot_symbols_state']['top_tradeable_symbols'] = [
        {'symbol': 'BTC', 'score': 120, 'rank': 1, 'sources': ['holding'], 'reasons': ['existing_holding']},
        {'symbol': 'ETH', 'score': 86, 'rank': 2, 'sources': ['social'], 'reasons': ['high_social_heat', 'multi_account_discussion']},
        {'symbol': 'RAVE', 'score': 68, 'rank': 3, 'sources': ['holding'], 'reasons': ['existing_holding']},
        {'symbol': 'SOL', 'score': 12, 'rank': 4, 'sources': ['cmc'], 'reasons': ['cmc_trending_symbol', 'okx_tradable_contract']},
    ]

    triggers = mod.build_triggers(context)

    assert triggers['llm_wake_required'] is False
    assert triggers['hot_symbols_ranking'] == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'source': 'social_hot_list',
            'priority': 'high',
            'reasons': ['high_social_heat', 'multi_account_discussion'],
        },
        {
            'symbol': 'RAVE',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'SOL',
            'source': 'cmc_trending_okx_listed',
            'priority': 'medium',
            'reasons': ['cmc_trending_symbol', 'okx_tradable_contract'],
        },
    ]
    assert set(triggers) == {'generated_at', 'schema_version', 'llm_wake_required', 'llm_wake_triggers', 'observe_only_triggers', 'hot_symbols_ranking', 'wake_state'}


def test_build_triggers_hot_symbols_ranking_excludes_security_event_only_symbol_promotion():
    mod = load_module()
    context = sample_context()
    context['macro']['regime'] = 'neutral'
    context['macro']['regime_bias'] = 'neutral'
    context['macro']['geo_risk'] = 'medium'
    context['macro']['event_window'] = False
    context['crypto_news']['news_risk'] = 'medium'
    context['social']['top_discussed_symbols'] = []
    context['social']['cmc_trending_symbols'] = []
    context['hot_symbols_state']['top_tradeable_symbols'] = [
        {'symbol': 'BTC', 'score': 120, 'rank': 1, 'sources': ['holding'], 'reasons': ['existing_holding']},
        {'symbol': 'RAVE', 'score': 68, 'rank': 2, 'sources': ['holding'], 'reasons': ['existing_holding']},
    ]
    context['crypto_news']['high_impact_events'] = [
        {
            'title': 'MASK exploit drains funds from treasury',
            'source': 'blockbeats',
            'event_domain': 'security',
            'importance': 'high',
            'holds_match': False,
            'novelty': 'new',
        }
    ]

    triggers = mod.build_triggers(context)

    assert triggers['hot_symbols_ranking'] == [
        {
            'symbol': 'BTC',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'RAVE',
            'source': 'holding',
            'priority': 'critical',
            'reasons': ['existing_holding'],
        },
    ]
