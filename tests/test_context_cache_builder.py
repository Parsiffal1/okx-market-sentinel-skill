from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/build_context_cache.py"
JIN10_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/jin10_fetch.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_jin10_event_window_ignores_low_crypto_relevance_eia_release():
    mod = load_module(JIN10_MODULE_PATH, 'jin10_fetch_for_context_tests')

    payload = mod.build_macro_payload(
        flash_items=[],
        news_items=[],
        calendar_items=[
            {
                'country': '美国',
                'title': 'EIA原油库存',
                'importance': 5,
                'pub_time': '2026-04-22 22:30',
            }
        ],
        now=datetime(2026, 4, 22, 14, 0, tzinfo=timezone.utc),
    )

    assert payload['event_window'] is False
    assert payload['event_pre_release'] is False
    assert payload['event_recent_release'] is False


def test_normalize_event_fingerprint_deduplicates_same_title_across_sources_when_no_event_id_exists():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_fingerprint')

    first = mod.normalize_event_fingerprint({'title': 'RAVE exploit update', 'source': 'opennews'})
    second = mod.normalize_event_fingerprint({'title': 'RAVE exploit update', 'source': 'okx_news'})

    assert first == second


def test_merge_context_uses_layered_macro_aggregation_and_normalizes_sentiment_indicator():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:58:00+00:00',
            'data': {
                'macro': {
                    'geo_risk': 'medium',
                    'event_window': False,
                    'event_pre_release': False,
                    'event_recent_release': False,
                    'macro_summary': ['特朗普称将继续评估伊朗停火安排'],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:58:00+00:00',
            'data': {
                'macro': {
                    'usd_strength': 'weak',
                    'us10y_pressure': 'low',
                    'm2_trend': 'expanding',
                    'macro_summary': ['KelpDAO黑客已基本将1.75亿美元ETH洗钱为BTC'],
                },
                'crypto_news': {
                    'market_bias': 'slightly_bullish',
                    'high_impact_events': [
                        {'title': 'KelpDAO黑客已基本将1.75亿美元ETH洗钱为BTC', 'impact': 'bearish', 'source': 'blockbeats'}
                    ],
                },
                'market_context': {
                    'btc_etf_flow': 'positive',
                    'stablecoin_liquidity': 'expanding',
                    'onchain_tx_trend': 'positive',
                    'contract_oi_environment': 'positive',
                    'sentiment_indicator': 'positive',
                },
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:58:30+00:00',
            'data': {
                'has_positions': True,
                'prioritized_symbols': ['BTC', 'RAVE'],
                'accounts': {
                    'live': {'symbols': [], 'positions': []},
                    'demo': {'symbols': ['BTC', 'RAVE'], 'positions': [{'instId': 'BTC-USDT-SWAP'}, {'instId': 'RAVE-USDT-SWAP'}]},
                },
            },
        },
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:57:00+00:00',
            'data': {
                'market_bias': 'slightly_bullish',
                'news_risk': 'low',
                'high_impact_events': [
                    {'title': 'KelpDAO attack response: Aave raises USDC rates after exploit', 'impact': 'bearish', 'source': 'odaily_flash'}
                ],
            },
        },
        'opennews': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:56:00+00:00',
            'data': {
                'market_bias': 'bullish',
                'news_risk': 'high',
                'high_impact_events': [
                    {'title': 'major exploit postmortem released after patch deployed', 'impact': 'bearish', 'source': 'opennews', 'score': 92}
                ],
            },
        },
        'opentwitter': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:55:00+00:00',
            'data': {
                'market_narrative': 'active',
                'watch_accounts': [],
                'social_risk': 'low',
            },
        },
    }

    ctx = mod.merge_context(raw_data, {
        'staleness_threshold_minutes': {},
        'macro_regime_rules': {
            'score_to_regime': {'bullish_min': 2, 'bearish_max': -2},
            'geo_risk_penalty': {'medium': -1, 'high': -2},
        },
    })

    assert ctx['macro']['regime'] == 'bullish'
    assert ctx['macro']['regime_bias'] == 'bullish'
    assert ctx['macro']['risk_state'] == 'medium'
    assert ctx['holdings']['has_positions'] is True
    assert ctx['holdings']['prioritized_symbols'] == ['BTC', 'RAVE']
    assert ctx['macro']['macro_summary'] == ['特朗普称将继续评估伊朗停火安排']
    assert ctx['macro']['crypto_native_risk_summary'] == []
    assert ctx['crypto_news']['news_risk'] == 'high'
    assert ctx['market_state'] == {
        'updated_at': '2026-04-22T14:58:00+00:00',
        'market_sentiment': 'bullish',
        'sentiment_confidence': 1.0,
        'risk_state': 'medium',
        'geo_risk': 'medium',
        'event_window': False,
        'macro_drivers': ['特朗普称将继续评估伊朗停火安排'],
        'crypto_native_risk_drivers': [],
        'summary': ['特朗普称将继续评估伊朗停火安排'],
    }
    assert ctx['holdings_state']['has_positions'] is True
    assert ctx['holdings_state']['prioritized_symbols'] == ['BTC', 'RAVE']
    assert ctx['holdings_state']['symbol_risk'] == [
        {
            'symbol': 'BTC',
            'risk_state': 'medium',
            'relevant_event_count': 1,
            'relevant_social_heat': 0,
            'macro_alignment': 'bullish',
            'reasons': ['global_market_risk_medium'],
        },
        {
            'symbol': 'RAVE',
            'risk_state': 'medium',
            'relevant_event_count': 0,
            'relevant_social_heat': 0,
            'macro_alignment': 'bullish',
            'reasons': ['global_market_risk_medium'],
        },
    ]
    assert ctx['hot_symbols_state'] == {
        'updated_at': '2026-04-22T14:58:30+00:00',
        'top_tradeable_symbols': [
            {
                'symbol': 'BTC',
                'score': 120,
                'rank': 1,
                'sources': ['holding'],
                'reasons': ['existing_holding'],
            },
            {
                'symbol': 'RAVE',
                'score': 120,
                'rank': 2,
                'sources': ['holding'],
                'reasons': ['existing_holding'],
            },
        ],
    }
    security_events = {(item['title'], item['source'], item['state']) for item in ctx['crypto_news']['security_events']}
    assert security_events == {
        (
            'KelpDAO attack response: Aave raises USDC rates after exploit',
            'odaily_flash',
            'post_exploit_active',
        ),
        (
            'major exploit postmortem released after patch deployed',
            'opennews',
            'postmortem',
        ),
        (
            'KelpDAO黑客已基本将1.75亿美元ETH洗钱为BTC',
            'blockbeats',
            'postmortem',
        ),
    }
    assert ctx['market_context']['sentiment_indicator'] == 'slightly_bullish'



def test_merge_context_builds_holdings_focused_social_and_signal_views():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_holdings_views')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:58:00+00:00',
            'data': {'macro': {'geo_risk': 'low', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}},
        },
        'blockbeats': {'status': 'ok', 'updated_at': '2026-04-22T14:58:00+00:00', 'data': {'macro': {}, 'crypto_news': {}, 'market_context': {}}},
        'cmc': {'status': 'ok', 'updated_at': '2026-04-22T14:58:00+00:00', 'data': {'macro': {}, 'market_context': {}, 'social': {'cmc_trending_symbols': ['RAVE']}}},
        'moss_xsignal': {'status': 'ok', 'updated_at': '2026-04-22T14:58:00+00:00', 'data': {'macro': {}, 'social': {}}},
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:58:30+00:00',
            'data': {
                'has_positions': True,
                'prioritized_symbols': ['BTC', 'RAVE'],
                'accounts': {
                    'live': {'symbols': ['BTC'], 'positions': [{'instId': 'BTC-USDT-SWAP'}]},
                    'demo': {'symbols': ['RAVE'], 'positions': [{'instId': 'RAVE-USDT-SWAP'}]},
                },
            },
        },
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'medium',
                'high_impact_events': [
                    {'title': 'BTC ETF inflows accelerate as desks re-risk', 'impact': 'bullish', 'source': 'okx_news'},
                    {'title': 'RAVE ecosystem treasury update draws attention', 'impact': 'neutral', 'source': 'okx_news'},
                ],
            },
        },
        'opennews': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:56:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'low',
                'high_impact_events': [
                    {'title': 'Macro digest remains stable', 'impact': 'neutral', 'source': 'opennews'}
                ],
            },
        },
        'opentwitter': {
            'status': 'ok',
            'updated_at': '2026-04-22T14:55:00+00:00',
            'data': {
                'market_narrative': 'active',
                'watch_accounts': [],
                'social_risk': 'low',
                'symbol_mentions': [
                    {'symbol': 'BTC', 'mention_count': 4, 'unique_accounts': 2, 'weighted_heat': 92000},
                    {'symbol': 'ETH', 'mention_count': 5, 'unique_accounts': 3, 'weighted_heat': 130000},
                    {'symbol': 'RAVE', 'mention_count': 2, 'unique_accounts': 1, 'weighted_heat': 21000},
                ],
                'top_discussed_symbols': ['ETH', 'BTC', 'RAVE'],
            },
        },
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}, 'macro_regime_rules': {}})

    assert ctx['social']['holdings_symbol_mentions'] == [
        {'symbol': 'BTC', 'mention_count': 4, 'unique_accounts': 2, 'weighted_heat': 92000},
        {'symbol': 'RAVE', 'mention_count': 2, 'unique_accounts': 1, 'weighted_heat': 21000},
    ]
    assert ctx['social']['holdings_top_discussed_symbols'] == ['BTC', 'RAVE']
    assert [item['title'] for item in ctx['signal_inputs']['held_symbol_risk_events']] == [
        'BTC ETF inflows accelerate as desks re-risk',
        'RAVE ecosystem treasury update draws attention',
    ]
    assert ctx['signal_inputs']['held_symbol_social_heat'] == [
        {'symbol': 'BTC', 'mention_count': 4, 'unique_accounts': 2, 'weighted_heat': 92000},
        {'symbol': 'RAVE', 'mention_count': 2, 'unique_accounts': 1, 'weighted_heat': 21000},
    ]



def test_extract_event_symbols_can_recognize_non_major_uppercase_token_symbols():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_symbol_extraction')

    assert mod.extract_event_symbols({'title': 'RAVE bridge exploit drains funds from protocol treasury'}) == ['RAVE']
    assert mod.extract_event_symbols({'title': 'Hyperliquid whale opens new BTC short while ETH stays rangebound'}) == ['BTC', 'ETH']



def test_classify_security_event_state_distinguishes_live_active_and_postmortem():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_security_states')

    assert mod.classify_security_event_state('Protocol suffers exploit, attacker draining funds in real time') == 'live_exploit'
    assert mod.classify_security_event_state('Exchange hack response continues, attacker address still moving funds during incident response') == 'post_exploit_active'
    assert mod.classify_security_event_state('KelpDAO黑客完成洗币，近2000枚BTC转出') == 'postmortem'
    assert mod.classify_security_event_state('Full exploit postmortem published after patch and reimbursement plan') == 'postmortem'
    assert mod.classify_security_event_state('CertiK warns phishing may rise in 2026') == 'background'


def test_classify_macro_regime_returns_unknown_when_all_inputs_missing():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_unknowns')

    assert mod.classify_macro_regime(
        {
            'usd_strength': 'unknown',
            'us10y_pressure': 'unknown',
            'm2_trend': 'unknown',
            'geo_risk': 'unknown',
            'fear_greed_classification': 'unknown',
            'market_breadth': 'unknown',
            'event_pre_release': False,
            'event_recent_release': False,
        },
        {},
    ) == 'unknown'


def test_classify_macro_regime_can_use_cmc_sentiment_and_breadth_to_reach_bullish():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_cmc_regime_on')

    assert mod.classify_macro_regime(
        {
            'usd_strength': 'unknown',
            'us10y_pressure': 'unknown',
            'm2_trend': 'unknown',
            'geo_risk': 'unknown',
            'fear_greed_classification': 'greed',
            'market_breadth': 'broad_risk_on',
            'event_pre_release': False,
            'event_recent_release': False,
        },
        {
            'score_to_regime': {'bullish_min': 2, 'bearish_max': -2},
            'fear_greed_score': {'greed': 1},
            'market_breadth_score': {'broad_risk_on': 1},
        },
    ) == 'bullish'


def test_classify_macro_regime_treats_invalid_values_as_unknown():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_invalid')

    assert mod.classify_macro_regime(
        {
            'usd_strength': 'sideways',
            'us10y_pressure': None,
            'm2_trend': '',
            'geo_risk': 'elevated',
            'event_pre_release': False,
            'event_recent_release': False,
        },
        {},
    ) == 'unknown'


def test_classify_macro_regime_ignores_slow_m2_trend_as_direct_intraday_signal():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_ignore_m2')

    assert mod.classify_macro_regime(
        {
            'usd_strength': 'unknown',
            'us10y_pressure': 'unknown',
            'm2_trend': 'expanding',
            'geo_risk': 'unknown',
            'fear_greed_classification': 'unknown',
            'market_breadth': 'unknown',
            'event_pre_release': False,
            'event_recent_release': False,
        },
        {
            'score_to_regime': {'bullish_min': 1, 'bearish_max': -1},
        },
    ) == 'unknown'


def test_classify_regime_bias_uses_moss_sentiment_without_large_cap_leadership():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_regime_bias')

    assert mod.classify_regime_bias(
        {
            'usd_strength': 'weak',
            'us10y_pressure': 'low',
            'geo_risk': 'low',
            'event_window': False,
            'fear_greed_classification': 'greed',
            'market_breadth': 'broad_risk_on',
            'moss_sentiment_today': 68,
            'large_cap_leadership': 'btc_leading',
        }
    ) == 'bullish'


def test_classify_regime_bias_can_stay_neutral_when_risk_is_high_but_direction_mixed():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_regime_bias_neutral')

    assert mod.classify_regime_bias(
        {
            'usd_strength': 'strong',
            'us10y_pressure': 'medium',
            'geo_risk': 'high',
            'event_window': False,
            'fear_greed_classification': 'greed',
            'market_breadth': 'broad_risk_on',
            'moss_sentiment_today': 32,
        }
    ) == 'neutral'


def test_classify_risk_state_requires_extreme_gate_not_just_score_stack():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_risk_state_gate')

    assert mod.classify_risk_state(
        {
            'geo_risk': 'high',
            'event_pre_release': False,
            'event_recent_release': False,
            'news_risk': 'high',
            'security_events': [{'state': 'postmortem'}],
            'fear_greed_classification': 'greed',
            'moss_sentiment_today': 32,
        }
    ) == 'medium'


def test_classify_risk_state_requires_more_stack_before_high():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_risk_state_high_bar')

    assert mod.classify_risk_state(
        {
            'geo_risk': 'high',
            'event_pre_release': False,
            'event_recent_release': False,
            'news_risk': 'medium',
            'security_events': [],
            'fear_greed_classification': 'neutral',
            'moss_sentiment_today': 50,
        }
    ) == 'medium'


def test_classify_risk_state_promotes_live_exploit_to_extreme():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_risk_state_extreme')

    assert mod.classify_risk_state(
        {
            'geo_risk': 'medium',
            'event_pre_release': False,
            'event_recent_release': False,
            'news_risk': 'high',
            'security_events': [{'state': 'live_exploit'}],
            'fear_greed_classification': 'neutral',
            'moss_sentiment_today': 50,
        }
    ) == 'extreme'


def test_rank_news_events_prioritizes_new_holdings_related_event_over_old_source_order():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_news_ranking')

    previous_state = {
        'events': {
            'old-btc-event': {
                'title': 'Old BTC ETF article',
                'source': 'okx_news',
                'symbols': ['BTC'],
                'first_seen_at': '2026-04-23T10:00:00+00:00',
                'last_seen_at': '2026-04-23T11:00:00+00:00',
                'seen_count': 3,
                'last_score': 12.0,
            }
        }
    }
    holdings_symbols = ['ETH', 'BTC']
    now = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
    events = [
        {
            'title': 'Old BTC ETF article',
            'source': 'okx_news',
            'impact': 'high',
            'id': 'old-btc-event',
            'published_at': '2026-04-23T11:45:00+00:00',
        },
        {
            'title': 'Dormant whale spends $7M to buy 3,000 ETH',
            'source': 'blockbeats',
            'impact': 'high',
            'id': 'new-eth-whale',
            'published_at': '2026-04-23T11:55:00+00:00',
        },
    ]

    ranked = mod.rank_news_events(events, holdings_symbols=holdings_symbols, previous_state=previous_state, now=now)

    assert ranked[0]['title'] == 'Dormant whale spends $7M to buy 3,000 ETH'
    assert ranked[0]['novelty'] == 'new'
    assert ranked[0]['holds_match'] is True
    assert ranked[1]['title'] == 'Old BTC ETF article'
    assert ranked[1]['novelty'] == 'seen'



def test_update_news_event_state_tracks_first_last_seen_and_seen_count():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_news_state')

    previous_state = {
        'events': {
            'old-btc-event': {
                'title': 'Old BTC ETF article',
                'source': 'okx_news',
                'symbols': ['BTC'],
                'first_seen_at': '2026-04-23T10:00:00+00:00',
                'last_seen_at': '2026-04-23T11:00:00+00:00',
                'seen_count': 3,
                'last_score': 12.0,
            }
        }
    }
    ranked_events = [
        {
            'fingerprint': 'old-btc-event',
            'title': 'Old BTC ETF article',
            'source': 'okx_news',
            'symbols': ['BTC'],
            'event_score': 8.0,
        },
        {
            'fingerprint': 'new-eth-whale',
            'title': 'Dormant whale spends $7M to buy 3,000 ETH',
            'source': 'blockbeats',
            'symbols': ['ETH'],
            'event_score': 16.0,
        },
    ]

    next_state = mod.update_news_event_state(previous_state, ranked_events, now_iso='2026-04-23T12:00:00+00:00')

    assert next_state['events']['old-btc-event']['first_seen_at'] == '2026-04-23T10:00:00+00:00'
    assert next_state['events']['old-btc-event']['last_seen_at'] == '2026-04-23T12:00:00+00:00'
    assert next_state['events']['old-btc-event']['seen_count'] == 4
    assert next_state['events']['new-eth-whale']['first_seen_at'] == '2026-04-23T12:00:00+00:00'
    assert next_state['events']['new-eth-whale']['last_seen_at'] == '2026-04-23T12:00:00+00:00'
    assert next_state['events']['new-eth-whale']['seen_count'] == 1



def test_merge_context_builds_new_and_watchlist_buckets_from_ranked_news():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_news_buckets')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []},
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {'title': 'Dormant whale spends $7M to buy 3,000 ETH', 'impact': 'high', 'source': 'blockbeats', 'id': 'new-eth-whale', 'published_at': '2026-04-23T11:55:00+00:00'},
                    ],
                },
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}},
        },
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'medium',
                'high_impact_events': [
                    {'title': 'Old BTC ETF article', 'impact': 'high', 'source': 'okx_news', 'id': 'old-btc-event', 'published_at': '2026-04-23T11:45:00+00:00'},
                ],
            },
        },
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }
    previous_state = {
        'events': {
            'old-btc-event': {
                'title': 'Old BTC ETF article',
                'source': 'okx_news',
                'symbols': ['BTC'],
                'first_seen_at': '2026-04-23T10:00:00+00:00',
                'last_seen_at': '2026-04-23T11:00:00+00:00',
                'seen_count': 3,
                'last_score': 12.0,
            }
        }
    }

    ctx, next_state = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}}, previous_news_state=previous_state, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc), return_news_state=True)

    assert ctx['crypto_news']['high_impact_events'][0]['title'] == 'Dormant whale spends $7M to buy 3,000 ETH'
    assert ctx['crypto_news']['new_high_impact_events'][0]['title'] == 'Dormant whale spends $7M to buy 3,000 ETH'
    assert ctx['crypto_news']['watchlist_events'][0]['title'] == 'Old BTC ETF article'
    assert next_state['events']['new-eth-whale']['seen_count'] == 1


def test_merge_context_hot_ranking_supports_all_okx_tradeable_contracts_not_only_crypto_symbols():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_all_okx_contracts')

    ctx = mod.default_context()
    ctx['holdings'] = {'prioritized_symbols': [], 'has_positions': False}
    ctx['social'] = {
        'symbol_mentions': [],
        'top_discussed_symbols': [],
        'cmc_trending_symbols': ['TON'],
        'okx_top_gainers': [
            {'symbol': 'AAPL', 'rank': 1},
            {'symbol': 'TON', 'rank': 2},
        ],
        'okx_top_oi': [
            {'symbol': 'ETH', 'rank': 1},
            {'symbol': 'XAU', 'rank': 2},
        ],
        'okx_oi_change': [
            {'symbol': 'CL', 'quadrant': 'oi_up_price_down', 'rank': 1},
        ],
        'okx_gainer_symbols': ['AAPL', 'TON'],
        'okx_top_oi_symbols': ['ETH', 'XAU'],
        'okx_oi_change_symbols': ['CL'],
    }

    ranking = mod.build_top_tradeable_symbols(ctx)

    assert [item['symbol'] for item in ranking[:5]] == ['TON', 'AAPL', 'CL', 'ETH', 'XAU']
    assert any(item['symbol'] == 'AAPL' and 'okx_top_gainer_24h' in item['reasons'] for item in ranking)
    assert any(item['symbol'] == 'CL' and 'okx_oi_short_build_quadrant' in item['reasons'] for item in ranking)
    assert any(item['symbol'] == 'XAU' and 'okx_top_oi_contract' in item['reasons'] for item in ranking)



def test_merge_context_builds_top_tradeable_symbols_from_holdings_social_and_cmc_inputs():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_top_tradeable_symbols')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'low', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {'status': 'ok', 'updated_at': '2026-04-23T11:59:00+00:00', 'data': {'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []}, 'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []}, 'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'}}},
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': True, 'prioritized_symbols': ['BTC'], 'accounts': {'live': {'symbols': ['BTC'], 'positions': []}, 'demo': {'symbols': [], 'positions': []}}}},
        'okx_market': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:20+00:00',
            'data': {
                'social': {
                    'okx_top_gainers': [
                        {'symbol': 'TON', 'instId': 'TON-USDT-SWAP', 'chg24hPct': 36.36, 'oiUsd': 3581058769.14, 'volUsd24h': 6128654487.55, 'fundingRate': -0.0001238, 'rank': 1},
                    ],
                    'okx_top_oi': [
                        {'symbol': 'ETH', 'instId': 'ETH-USDT-SWAP', 'chg24hPct': 1.59, 'oiUsd': 2903803937838.57, 'volUsd24h': 276578822819.25, 'fundingRate': 0.00005824, 'rank': 1},
                    ],
                    'okx_oi_change': [
                        {'symbol': 'TON', 'instId': 'TON-USDT-SWAP', 'oiUsd': 550000000.0, 'prevOiUsd': 420000000.0, 'oiDeltaUsd': 130000000.0, 'oiDeltaPct': 31.0, 'pxChgPct': 12.0, 'fundingRate': -0.0001238, 'volUsd24h': 6128654487.55, 'quadrant': 'oi_up_price_up', 'rank': 1},
                    ],
                    'okx_gainer_symbols': ['TON'],
                    'okx_top_oi_symbols': ['ETH'],
                    'okx_oi_change_symbols': ['TON'],
                }
            },
        },
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:55:00+00:00',
            'data': {
                'market_narrative': 'active',
                'watch_accounts': [],
                'social_risk': 'low',
                'symbol_mentions': [
                    {'symbol': 'ETH', 'unique_accounts': 3, 'weighted_heat': 125000},
                    {'symbol': 'SOL', 'unique_accounts': 1, 'weighted_heat': 70000},
                ],
                'top_discussed_symbols': ['ETH', 'SOL'],
            },
        },
        'cmc': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:54:00+00:00',
            'data': {
                'macro': {'fear_greed_classification': 'neutral', 'fear_greed_value': 50, 'altcoin_season_classification': 'neutral', 'altcoin_season_value': 40},
                'market_context': {'market_breadth': 'neutral', 'large_cap_leadership': 'btc_leading'},
                'social': {'cmc_trending_symbols': ['SOL', 'TON']},
            },
        },
        'moss_xsignal': {'status': 'ok', 'updated_at': '2026-04-23T11:53:00+00:00', 'data': {'macro': {'moss_sentiment_today': 50, 'moss_sentiment_bias': 'neutral'}, 'social': {'moss_available_dates': []}}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}})

    assert ctx['hot_symbols_state']['top_tradeable_symbols'] == [
        {
            'symbol': 'BTC',
            'score': 120,
            'rank': 1,
            'sources': ['holding'],
            'reasons': ['existing_holding'],
        },
        {
            'symbol': 'ETH',
            'score': 92,
            'rank': 2,
            'sources': ['social', 'okx_top_oi'],
            'reasons': ['high_social_heat', 'multi_account_discussion', 'okx_top_oi_contract'],
        },
        {
            'symbol': 'TON',
            'score': 57,
            'rank': 3,
            'sources': ['cmc', 'okx_oi_change', 'okx_top_gainers'],
            'reasons': ['cmc_trending_symbol', 'okx_oi_price_up_quadrant', 'okx_oi_change_leader', 'okx_top_gainer_24h'],
        },
        {
            'symbol': 'SOL',
            'score': 28,
            'rank': 4,
            'sources': ['social', 'cmc'],
            'reasons': ['social_symbol_mention', 'cmc_trending_symbol'],
        },
    ]



def test_merge_context_escalates_held_symbol_risk_for_live_security_event():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_holdings_live_security')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {'status': 'ok', 'updated_at': '2026-04-23T11:59:00+00:00', 'data': {'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []}, 'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []}, 'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'}}},
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': True, 'prioritized_symbols': ['RAVE'], 'accounts': {'live': {'symbols': ['RAVE'], 'positions': []}, 'demo': {'symbols': [], 'positions': []}}}},
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'high',
                'high_impact_events': [
                    {'title': 'RAVE bridge exploit drains funds from protocol treasury', 'impact': 'high', 'source': 'okx_news', 'id': 'rave-live-exploit', 'published_at': '2026-04-23T11:56:00+00:00'},
                ],
            },
        },
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
        'cmc': {'status': 'ok', 'updated_at': '2026-04-23T11:54:00+00:00', 'data': {'macro': {'fear_greed_classification': 'neutral', 'fear_greed_value': 50, 'altcoin_season_classification': 'neutral', 'altcoin_season_value': 40}, 'market_context': {'market_breadth': 'neutral', 'large_cap_leadership': 'btc_leading'}}},
        'moss_xsignal': {'status': 'ok', 'updated_at': '2026-04-23T11:53:00+00:00', 'data': {'macro': {'moss_sentiment_today': 50, 'moss_sentiment_bias': 'neutral'}, 'social': {'moss_available_dates': []}}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}})

    assert ctx['holdings_state']['symbol_risk'] == [
        {
            'symbol': 'RAVE',
            'risk_state': 'extreme',
            'relevant_event_count': 1,
            'relevant_social_heat': 0,
            'macro_alignment': 'neutral',
            'reasons': ['held_symbol_live_security_event'],
        }
    ]
    assert [event['title'] for event in ctx['signal_inputs']['holdings_related_new_events']] == [
        'RAVE bridge exploit drains funds from protocol treasury'
    ]



def test_merge_context_does_not_spread_live_security_risk_to_unmatched_held_symbols():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_holdings_live_security_isolated')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {'status': 'ok', 'updated_at': '2026-04-23T11:59:00+00:00', 'data': {'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []}, 'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []}, 'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'}}},
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': True, 'prioritized_symbols': ['BTC', 'RAVE'], 'accounts': {'live': {'symbols': ['BTC', 'RAVE'], 'positions': []}, 'demo': {'symbols': [], 'positions': []}}}},
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'high',
                'high_impact_events': [
                    {'title': 'RAVE bridge exploit drains funds from protocol treasury', 'impact': 'high', 'source': 'okx_news', 'id': 'rave-live-exploit', 'published_at': '2026-04-23T11:56:00+00:00'},
                ],
            },
        },
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
        'cmc': {'status': 'ok', 'updated_at': '2026-04-23T11:54:00+00:00', 'data': {'macro': {'fear_greed_classification': 'neutral', 'fear_greed_value': 50, 'altcoin_season_classification': 'neutral', 'altcoin_season_value': 40}, 'market_context': {'market_breadth': 'neutral', 'large_cap_leadership': 'btc_leading'}}},
        'moss_xsignal': {'status': 'ok', 'updated_at': '2026-04-23T11:53:00+00:00', 'data': {'macro': {'moss_sentiment_today': 50, 'moss_sentiment_bias': 'neutral'}, 'social': {'moss_available_dates': []}}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}})

    assert ctx['holdings_state']['symbol_risk'] == [
        {
            'symbol': 'BTC',
            'risk_state': 'extreme',
            'relevant_event_count': 0,
            'relevant_social_heat': 0,
            'macro_alignment': 'neutral',
            'reasons': ['global_market_risk_extreme'],
        },
        {
            'symbol': 'RAVE',
            'risk_state': 'extreme',
            'relevant_event_count': 1,
            'relevant_social_heat': 0,
            'macro_alignment': 'neutral',
            'reasons': ['held_symbol_live_security_event'],
        },
    ]



def test_merge_context_marks_held_altcoin_security_event_from_blockbeats_as_symbol_specific_risk():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_holdings_blockbeats_security')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []},
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {'title': 'RAVE bridge exploit drains funds from protocol treasury', 'impact': 'high', 'source': 'blockbeats', 'id': 'rave-live-exploit', 'published_at': '2026-04-23T11:56:00+00:00'},
                    ],
                },
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': True, 'prioritized_symbols': ['RAVE'], 'accounts': {'live': {'symbols': ['RAVE'], 'positions': []}, 'demo': {'symbols': [], 'positions': []}}}},
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
        'cmc': {'status': 'ok', 'updated_at': '2026-04-23T11:54:00+00:00', 'data': {'macro': {'fear_greed_classification': 'neutral', 'fear_greed_value': 50, 'altcoin_season_classification': 'neutral', 'altcoin_season_value': 40}, 'market_context': {'market_breadth': 'neutral', 'large_cap_leadership': 'btc_leading'}}},
        'moss_xsignal': {'status': 'ok', 'updated_at': '2026-04-23T11:53:00+00:00', 'data': {'macro': {'moss_sentiment_today': 50, 'moss_sentiment_bias': 'neutral'}, 'social': {'moss_available_dates': []}}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}})

    assert ctx['holdings_state']['symbol_risk'] == [
        {
            'symbol': 'RAVE',
            'risk_state': 'extreme',
            'relevant_event_count': 1,
            'relevant_social_heat': 0,
            'macro_alignment': 'neutral',
            'reasons': ['held_symbol_live_security_event'],
        }
    ]



def test_merge_context_deduplicates_security_followup_title_across_source_types():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_security_dedupe')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': ['KelpDAO黑客完成「洗币」，近2000枚BTC转出']},
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {'title': 'KelpDAO黑客完成「洗币」，近2000枚BTC转出', 'impact': 'high', 'source': 'blockbeats', 'id': 'kelp-followup', 'published_at': '2026-04-23T11:55:00+00:00'},
                    ],
                },
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['BTC'], 'positions': []}}},
        },
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'medium', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}}, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    security_titles = [item['title'] for item in ctx['crypto_news']['security_events']]
    assert security_titles == ['KelpDAO黑客完成「洗币」，近2000枚BTC转出']
    new_titles = [item['title'] for item in ctx['crypto_news']['new_high_impact_events']]
    assert new_titles == ['KelpDAO黑客完成「洗币」，近2000枚BTC转出']


def test_merge_context_includes_cmc_quant_signals_in_market_context():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_cmc_merge')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []},
                'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []},
                'market_context': {'btc_etf_flow': 'positive', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'negative', 'contract_oi_environment': 'positive', 'sentiment_indicator': 'neutral'},
            },
        },
        'cmc': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:10+00:00',
            'data': {
                'macro': {
                    'fear_greed_classification': 'fear',
                    'fear_greed_value': 32,
                    'altcoin_season_classification': 'btc_season',
                    'altcoin_season_value': 22,
                    'btc_dominance': 60.1,
                    'eth_dominance': 10.7,
                },
                'market_context': {
                    'market_breadth': 'broad_risk_off',
                    'large_cap_leadership': 'btc_leading',
                },
                'social': {
                    'cmc_trending_symbols': ['HYPE'],
                },
            },
        },
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': False, 'prioritized_symbols': [], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': [], 'positions': []}}}},
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'medium', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}})

    assert ctx['market_context']['fear_greed_classification'] == 'fear'
    assert ctx['market_context']['altcoin_season_classification'] == 'btc_season'
    assert ctx['market_context']['market_breadth'] == 'broad_risk_off'
    assert ctx['market_context']['large_cap_leadership'] == 'btc_leading'
    assert 'top_movers' not in ctx['market_context']
    assert ctx['social']['cmc_trending_symbols'] == ['HYPE']
    assert 'cmc' in ctx['market_context']['sources']
    assert 'cmc' in ctx['social']['sources']


def test_classify_event_domain_uses_event_meaning_not_source_name():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_semantic_domain')

    assert mod.classify_event_domain(
        '特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升',
        source='blockbeats',
    ) == 'geo'
    assert mod.classify_event_domain(
        'BlackRock spot BTC ETF records strong inflows for third straight day',
        source='jin10',
    ) == 'institutional'
    assert mod.classify_event_domain(
        'Protocol exploit drains funds from cross-chain bridge',
        source='okx_news',
    ) == 'security'



def test_classify_event_domains_returns_ordered_multi_label_semantics():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_multi_label_domains')

    assert mod.classify_event_domains(
        'Nasdaq rallies as BlackRock spot BTC ETF records strong inflows for third straight day',
        source='jin10',
    ) == ['geo', 'institutional']
    assert mod.classify_event_domains(
        'Tether freezes 344M USDT with law-enforcement support after bridge exploit drains funds',
        source='blockbeats',
    ) == ['security', 'regulation']



def test_normalize_raw_event_outputs_shared_semantic_schema():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_normalize_raw_event')

    previous_state = {'events': {}}
    now = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
    event = mod.normalize_raw_event(
        {
            'id': 'evt-1',
            'title': 'Dormant whale buys 3,000 ETH as ETF inflows accelerate',
            'summary': 'Large dormant wallet accumulates ETH while ETF demand remains firm.',
            'impact': 'high',
            'published_at': '2026-04-23T11:55:00+00:00',
        },
        source='blockbeats',
        source_type='news',
        holdings_symbols=['ETH', 'BTC'],
        previous_state=previous_state,
        now=now,
    )

    assert event['fingerprint'] == 'evt-1'
    assert event['source'] == 'blockbeats'
    assert event['source_type'] == 'news'
    assert event['title'] == 'Dormant whale buys 3,000 ETH as ETF inflows accelerate'
    assert event['summary'] == 'Large dormant wallet accumulates ETH while ETF demand remains firm.'
    assert event['symbols'] == ['ETH']
    assert event['event_domain'] == 'institutional'
    assert event['event_domains'] == ['institutional', 'crypto_native']
    assert event['event_subtype'] == 'etf_flow'
    assert event['event_subtypes'] == ['etf_flow', 'whale_activity']
    assert event['importance'] == 'high'
    assert event['holds_match'] is True
    assert event['novelty'] == 'new'
    assert isinstance(event['event_score'], float)



def test_build_semantic_event_pool_collects_events_across_sources_before_classification():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_semantic_event_pool')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:58:00+00:00',
            'data': {
                'macro': {
                    'macro_summary': ['特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升'],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {
                    'macro_summary': ['Tether freezes 344M USDT with law-enforcement support'],
                },
                'crypto_news': {
                    'high_impact_events': [
                        {'id': 'evt-eth-whale', 'title': 'Dormant whale buys 3,000 ETH', 'impact': 'high', 'published_at': '2026-04-23T11:55:00+00:00'},
                    ],
                },
            },
        },
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'high_impact_events': [
                    {'id': 'evt-exploit', 'title': 'Cross-chain bridge exploit drains funds', 'impact': 'high', 'published_at': '2026-04-23T11:50:00+00:00'},
                ],
            },
        },
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'high_impact_events': []}},
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}},
        },
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {}},
    }

    pool = mod.build_semantic_event_pool(
        raw_data,
        holdings_symbols=['ETH', 'BTC'],
        previous_state={'events': {}},
        now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc),
    )

    titles_to_domain = {event['title']: event['event_domain'] for event in pool}

    assert titles_to_domain['特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升'] == 'geo'
    assert titles_to_domain['Tether freezes 344M USDT with law-enforcement support'] == 'regulation'
    assert titles_to_domain['Dormant whale buys 3,000 ETH'] == 'crypto_native'
    assert titles_to_domain['Cross-chain bridge exploit drains funds'] == 'security'
    assert len(pool) == 4



def test_merge_context_routes_mixed_source_events_by_semantic_domain_not_source_bucket():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_phase2_routing')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:58:00+00:00',
            'data': {
                'macro': {
                    'geo_risk': 'medium',
                    'event_window': False,
                    'event_pre_release': False,
                    'event_recent_release': False,
                    'macro_summary': [
                        'BlackRock spot BTC ETF records strong inflows for third straight day',
                    ],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {
                    'usd_strength': 'neutral',
                    'us10y_pressure': 'medium',
                    'm2_trend': 'flat',
                    'macro_summary': [
                        '特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升',
                    ],
                },
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {
                            'id': 'evt-whale',
                            'title': 'Dormant whale buys 3,000 ETH',
                            'impact': 'high',
                            'source': 'blockbeats',
                            'published_at': '2026-04-23T11:55:00+00:00',
                        },
                    ],
                },
                'market_context': {
                    'btc_etf_flow': 'neutral',
                    'stablecoin_liquidity': 'flat',
                    'onchain_tx_trend': 'neutral',
                    'contract_oi_environment': 'neutral',
                    'sentiment_indicator': 'neutral',
                },
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}},
        },
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'medium',
                'high_impact_events': [
                    {
                        'id': 'evt-exploit',
                        'title': 'Cross-chain bridge exploit drains funds',
                        'impact': 'high',
                        'source': 'okx_news',
                        'published_at': '2026-04-23T11:50:00+00:00',
                    },
                ],
            },
        },
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}}, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert '特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升' in ctx['macro']['macro_summary']
    assert 'BlackRock spot BTC ETF records strong inflows for third straight day' not in ctx['macro']['macro_summary']
    assert 'BlackRock spot BTC ETF records strong inflows for third straight day' in ctx['crypto_news']['high_impact_events'][0]['title'] or any(
        item['title'] == 'BlackRock spot BTC ETF records strong inflows for third straight day'
        for item in ctx['crypto_news']['high_impact_events']
    )
    assert 'Dormant whale buys 3,000 ETH' in ctx['macro']['crypto_native_risk_summary']
    assert all(item['title'] != '特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升' for item in ctx['crypto_news']['high_impact_events'])



def test_classify_event_domain_does_not_treat_generic_usd_amounts_as_macro_signal():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_phase2a_domain')

    assert mod.classify_event_domain('Caladan报告：Web3游戏「烧掉」150亿美元，93% GameFi项目已失败') == 'noise'
    assert mod.classify_event_domain('美国天然气期货日内走低3.00%，现报2.640美元/百万英热。') == 'noise'
    assert mod.classify_event_domain('美国10年期国债收益率升至4.6%，美元指数走强') == 'geo'



def test_merge_context_applies_second_pass_macro_relevance_filter_after_domain_routing():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_phase2a_macro_filter')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:58:00+00:00',
            'data': {
                'macro': {
                    'geo_risk': 'medium',
                    'event_window': False,
                    'event_pre_release': False,
                    'event_recent_release': False,
                    'macro_summary': [
                        '美国10年期国债收益率升至4.6%，美元指数走强',
                        '美国天然气期货日内走低3.00%，现报2.640美元/百万英热。',
                    ],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {
                    'usd_strength': 'neutral',
                    'us10y_pressure': 'medium',
                    'm2_trend': 'flat',
                    'macro_summary': [
                        'Caladan报告：Web3游戏「烧掉」150亿美元，93% GameFi项目已失败',
                        '特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升',
                    ],
                },
                'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []},
                'market_context': {
                    'btc_etf_flow': 'neutral',
                    'stablecoin_liquidity': 'flat',
                    'onchain_tx_trend': 'neutral',
                    'contract_oi_environment': 'neutral',
                    'sentiment_indicator': 'neutral',
                },
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}},
        },
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'medium', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }
    rules = {
        'staleness_threshold_minutes': {},
        'macro_rules': {
            'macro_summary_relevance_keywords': ['特朗普', '霍尔木兹', '美债', '收益率', '美元指数'],
            'macro_summary_exclude_keywords': ['GameFi', 'Web3游戏', '天然气期货日内'],
        },
    }

    ctx = mod.merge_context(raw_data, rules, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert '特朗普称将重新评估伊朗停火进展，霍尔木兹航运风险上升' in ctx['macro']['macro_summary']
    assert '美国10年期国债收益率升至4.6%，美元指数走强' in ctx['macro']['macro_summary']
    assert 'Caladan报告：Web3游戏「烧掉」150亿美元，93% GameFi项目已失败' not in ctx['macro']['macro_summary']
    assert '美国天然气期货日内走低3.00%，现报2.640美元/百万英热。' not in ctx['macro']['macro_summary']



def test_classify_event_domain_keeps_us_equity_risk_proxies_and_crypto_related_stocks_but_rejects_unrelated_single_names():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_phase2b_equities')

    assert mod.classify_event_domain('纳斯达克指数盘初跌超1.2%，标普500 ETF（SPY）走弱，风险资产承压') == 'geo'
    assert mod.classify_event_domain('美股开盘后 CRCL 与 MSTR 齐跌，市场担忧加密风险偏好降温') == 'geo'
    assert mod.classify_event_domain('BMNR and COIN rally with crypto beta names after US open') == 'geo'
    assert mod.classify_event_domain('英伟达盘初涨超3%，苹果续创历史新高') == 'noise'



def test_is_macro_summary_candidate_filters_promo_noise_but_keeps_us_equity_sentiment_proxies():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_phase2b_macro_candidate')

    macro_rules = {
        'macro_summary_relevance_keywords': ['纳斯达克', '标普500', 'qqq', 'spy', 'crcl', 'bmnr', 'mstr', 'coin', '美股开盘', '美股收盘', '盘初'],
        'macro_summary_exclude_keywords': ['立即观看', '正在讲解中', '直播', '苹果', '英伟达'],
    }

    assert mod.is_macro_summary_candidate('纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱', macro_rules) is True
    assert mod.is_macro_summary_candidate('美股开盘后 CRCL 与 MSTR 齐跌，市场担忧加密风险偏好降温', macro_rules) is True
    assert mod.is_macro_summary_candidate('国际现货黄金跌势震荡中！美联储年内或降息？正在讲解中，立即观看！', macro_rules) is False
    assert mod.is_macro_summary_candidate('英伟达盘初涨超3%，苹果续创历史新高', macro_rules) is False



def test_merge_context_keeps_us_equity_open_close_and_crypto_proxy_moves_in_macro_summary():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_phase2b_macro_routing')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:58:00+00:00',
            'data': {
                'macro': {
                    'geo_risk': 'medium',
                    'event_window': False,
                    'event_pre_release': False,
                    'event_recent_release': False,
                    'macro_summary': [
                        '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压',
                        '英伟达盘初涨超3%，苹果续创历史新高',
                        '国际现货黄金跌势震荡中！美联储年内或降息？正在讲解中，立即观看！',
                    ],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {
                    'usd_strength': 'neutral',
                    'us10y_pressure': 'medium',
                    'm2_trend': 'flat',
                    'macro_summary': [
                        '美股开盘后 CRCL 与 MSTR 齐跌，市场担忧加密风险偏好降温',
                        'BMNR and COIN rally with crypto beta names after US open',
                    ],
                },
                'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []},
                'market_context': {
                    'btc_etf_flow': 'neutral',
                    'stablecoin_liquidity': 'flat',
                    'onchain_tx_trend': 'neutral',
                    'contract_oi_environment': 'neutral',
                    'sentiment_indicator': 'neutral',
                },
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}},
        },
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'medium', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }
    rules = {
        'staleness_threshold_minutes': {},
        'macro_rules': {
            'macro_summary_relevance_keywords': ['纳斯达克', '纳指', '标普500', 'qqq', 'spy', 'crcl', 'bmnr', 'mstr', 'coin', '美股开盘', '美股收盘', '盘初', '美股'],
            'macro_summary_exclude_keywords': ['立即观看', '正在讲解中', '直播', '苹果', '英伟达'],
        },
    }

    ctx = mod.merge_context(raw_data, rules, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压' in ctx['macro']['macro_summary']
    assert '美股开盘后 CRCL 与 MSTR 齐跌，市场担忧加密风险偏好降温' in ctx['macro']['macro_summary']
    assert 'BMNR and COIN rally with crypto beta names after US open' in ctx['macro']['macro_summary']
    assert '英伟达盘初涨超3%，苹果续创历史新高' not in ctx['macro']['macro_summary']
    assert '国际现货黄金跌势震荡中！美联储年内或降息？正在讲解中，立即观看！' not in ctx['macro']['macro_summary']



def test_extract_security_events_accepts_multi_label_security_items_even_when_primary_domain_differs():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_multi_label_security_lane')

    events = [
        {
            'title': 'Tether freezes 344M USDT with law-enforcement support after bridge exploit drains funds',
            'source': 'blockbeats',
            'event_domain': 'regulation',
            'event_domains': ['regulation', 'security'],
        },
        {
            'title': 'BlackRock spot BTC ETF records strong inflows',
            'source': 'jin10',
            'event_domain': 'institutional',
            'event_domains': ['institutional'],
        },
    ]

    security_events = mod.extract_security_events(events, limit=10)

    assert security_events == [
        {
            'title': 'Tether freezes 344M USDT with law-enforcement support after bridge exploit drains funds',
            'source': 'blockbeats',
            'state': 'live_exploit',
        }
    ]



def test_merge_context_routes_multi_label_events_into_both_macro_and_crypto_native_views():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_multi_label_routing')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'low', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []},
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {
                            'id': 'evt-multi',
                            'title': 'Nasdaq rallies as BlackRock spot BTC ETF records strong inflows for third straight day',
                            'impact': 'high',
                            'source': 'blockbeats',
                            'published_at': '2026-04-23T11:55:00+00:00',
                        },
                    ],
                },
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['BTC'], 'positions': []}}},
        },
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'medium', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}, 'macro_rules': {}}, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert 'Nasdaq rallies as BlackRock spot BTC ETF records strong inflows for third straight day' in ctx['macro']['macro_summary']
    assert 'Nasdaq rallies as BlackRock spot BTC ETF records strong inflows for third straight day' in ctx['macro']['crypto_native_risk_summary']



def test_extract_security_events_only_uses_semantic_security_domain_items():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_semantic_security_lane')

    events = [
        {
            'title': 'Bridge exploit drains funds from protocol treasury',
            'source': 'okx_news',
            'event_domain': 'security',
        },
        {
            'title': 'Tether freezes 344M USDT with law-enforcement support',
            'source': 'blockbeats',
            'event_domain': 'regulation',
        },
        {
            'title': 'BlackRock spot BTC ETF records strong inflows',
            'source': 'jin10',
            'event_domain': 'institutional',
        },
    ]

    security_events = mod.extract_security_events(events, limit=10)

    assert security_events == [
        {
            'title': 'Bridge exploit drains funds from protocol treasury',
            'source': 'okx_news',
            'state': 'live_exploit',
        }
    ]



def test_merge_context_security_events_are_derived_from_semantic_security_lane_only():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_security_lane_routing')

    raw_data = {
        'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'medium', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {'usd_strength': 'neutral', 'us10y_pressure': 'medium', 'm2_trend': 'flat', 'macro_summary': []},
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {'id': 'evt-freeze', 'title': 'Tether freezes 344M USDT with law-enforcement support', 'impact': 'high', 'source': 'blockbeats', 'published_at': '2026-04-23T11:55:00+00:00'},
                    ],
                },
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:30+00:00',
            'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}},
        },
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'high',
                'high_impact_events': [
                    {'id': 'evt-exploit', 'title': 'Bridge exploit drains funds from protocol treasury', 'impact': 'high', 'source': 'okx_news', 'published_at': '2026-04-23T11:50:00+00:00'},
                ],
            },
        },
        'opennews': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:56:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'low',
                'high_impact_events': [
                    {'id': 'evt-etf', 'title': 'BlackRock spot BTC ETF records strong inflows', 'impact': 'high', 'source': 'opennews', 'published_at': '2026-04-23T11:48:00+00:00'},
                ],
            },
        },
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }

    ctx = mod.merge_context(raw_data, {'staleness_threshold_minutes': {}, 'macro_rules': {}}, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert ctx['crypto_news']['security_events'] == [
        {
            'title': 'Bridge exploit drains funds from protocol treasury',
            'source': 'okx_news',
            'state': 'live_exploit',
        }
    ]



def test_build_macro_summary_view_deduplicates_compresses_and_buckets_semantic_macro_items():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_macro_summary_view')

    events = [
        {
            'title': '【伊朗称已制定针对美方及其盟友的反击目标清单】金十数据4月23日讯，当地时间23日伊朗方面消息，在外交受挫背景下，伊朗已制定回应目标清单。',
            'event_domain': 'geo',
            'event_subtype': 'state_policy',
            'event_score': 10.0,
        },
        {
            'title': '伊朗称已制定针对美方及其盟友的反击目标清单',
            'event_domain': 'geo',
            'event_subtype': 'state_policy',
            'event_score': 9.0,
        },
        {
            'title': '美国10年期国债收益率升至4.6%，美元指数走强',
            'event_domain': 'geo',
            'event_subtype': 'macro_rates',
            'event_score': 8.0,
        },
        {
            'title': '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压',
            'event_domain': 'geo',
            'event_subtype': 'us_equity_risk_sentiment',
            'event_score': 7.0,
        },
    ]

    summary = mod.build_macro_summary_view(events, limit=6)

    assert summary['summary'] == [
        '伊朗称已制定针对美方及其盟友的反击目标清单',
        '美国10年期国债收益率升至4.6%，美元指数走强',
        '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压',
    ]
    assert summary['buckets'] == {
        'geo': ['伊朗称已制定针对美方及其盟友的反击目标清单'],
        'macro_financial': ['美国10年期国债收益率升至4.6%，美元指数走强'],
        'us_equity_sentiment': ['纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压'],
    }



def test_classify_event_domain_distinguishes_coinbase_premium_from_coin_stock_proxy():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_macro_token_matching')

    assert mod.classify_event_domain('Buying sentiment in the US market continues to pick up, with the Coinbase Bitcoin Premium Index being positive for 12 consecutive days') == 'flow'
    assert mod.classify_macro_bucket({'title': 'H100 signed a binding strategic acquisition agreement, and its Bitcoin holdings are expected to increase to 3,500', 'event_subtype': 'geo'}) == 'us_equity_sentiment'



def test_merge_context_writes_deduped_macro_summary_and_summary_buckets():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_macro_summary_buckets')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:58:00+00:00',
            'data': {
                'macro': {
                    'geo_risk': 'high',
                    'event_window': False,
                    'event_pre_release': False,
                    'event_recent_release': False,
                    'macro_summary': [
                        '【伊朗称已制定针对美方及其盟友的反击目标清单】金十数据4月23日讯，当地时间23日伊朗方面消息，在外交受挫背景下，伊朗已制定回应目标清单。',
                        '美国10年期国债收益率升至4.6%，美元指数走强',
                        '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压',
                    ],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {
                    'usd_strength': 'strong',
                    'us10y_pressure': 'high',
                    'm2_trend': 'flat',
                    'macro_summary': [
                        '伊朗称已制定针对美方及其盟友的反击目标清单',
                    ],
                },
                'crypto_news': {'market_bias': 'neutral', 'high_impact_events': []},
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}}},
        'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'medium', 'high_impact_events': []}},
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }
    rules = {
        'staleness_threshold_minutes': {},
        'macro_rules': {
            'macro_summary_relevance_keywords': ['伊朗', '收益率', '美元指数', '纳斯达克', 'QQQ', 'SPY'],
            'macro_summary_exclude_keywords': [],
        },
    }

    ctx = mod.merge_context(raw_data, rules, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert ctx['macro']['macro_summary'] == [
        '伊朗称已制定针对美方及其盟友的反击目标清单',
        '美国10年期国债收益率升至4.6%，美元指数走强',
        '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压',
    ]
    assert ctx['macro']['summary_buckets'] == {
        'geo': ['伊朗称已制定针对美方及其盟友的反击目标清单'],
        'macro_financial': ['美国10年期国债收益率升至4.6%，美元指数走强'],
        'us_equity_sentiment': ['纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压'],
    }



def test_merge_context_writes_semantic_top_level_compatibility_keys():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_semantic_top_level_keys')

    raw_data = {
        'jin10': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:58:00+00:00',
            'data': {
                'macro': {
                    'geo_risk': 'high',
                    'event_window': True,
                    'event_pre_release': True,
                    'event_recent_release': False,
                    'macro_summary': [
                        '伊朗称已制定针对美方及其盟友的反击目标清单',
                        '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱，风险资产承压',
                    ],
                }
            },
        },
        'blockbeats': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:59:00+00:00',
            'data': {
                'macro': {
                    'usd_strength': 'strong',
                    'us10y_pressure': 'high',
                    'm2_trend': 'flat',
                    'macro_summary': [],
                },
                'crypto_news': {
                    'market_bias': 'neutral',
                    'high_impact_events': [
                        {'id': 'evt-freeze', 'title': 'Tether freezes 344M USDT with law-enforcement support', 'impact': 'high', 'source': 'blockbeats', 'published_at': '2026-04-23T11:55:00+00:00'},
                    ],
                },
                'market_context': {'btc_etf_flow': 'neutral', 'stablecoin_liquidity': 'flat', 'onchain_tx_trend': 'neutral', 'contract_oi_environment': 'neutral', 'sentiment_indicator': 'neutral'},
            },
        },
        'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:59:30+00:00', 'data': {'has_positions': True, 'prioritized_symbols': ['ETH', 'BTC'], 'accounts': {'live': {'symbols': [], 'positions': []}, 'demo': {'symbols': ['ETH', 'BTC'], 'positions': []}}}},
        'okx_news': {
            'status': 'ok',
            'updated_at': '2026-04-23T11:57:00+00:00',
            'data': {
                'market_bias': 'neutral',
                'news_risk': 'high',
                'high_impact_events': [
                    {'id': 'evt-exploit', 'title': 'Bridge exploit drains funds from protocol treasury', 'impact': 'high', 'source': 'okx_news', 'published_at': '2026-04-23T11:50:00+00:00'},
                ],
            },
        },
        'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
        'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'market_narrative': 'active', 'watch_accounts': [], 'social_risk': 'low'}},
    }
    rules = {
        'staleness_threshold_minutes': {},
        'macro_rules': {
            'macro_summary_relevance_keywords': ['伊朗', '纳斯达克', 'QQQ', 'SPY'],
            'macro_summary_exclude_keywords': [],
        },
    }

    ctx = mod.merge_context(raw_data, rules, previous_news_state={'events': {}}, now=datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc))

    assert ctx['macro_context']['summary'] == ctx['macro']['macro_summary']
    assert ctx['macro_context']['summary_buckets'] == ctx['macro']['summary_buckets']
    assert ctx['macro_context']['regime'] == ctx['macro']['regime']
    assert ctx['security']['events'] == ctx['crypto_news']['security_events']
    assert ctx['signal_inputs']['holdings_related_new_events'] == [
        event for event in ctx['crypto_news']['new_high_impact_events'] if event.get('holds_match')
    ]
    assert ctx['signal_inputs']['us_equity_risk_events'] == ctx['macro_context']['summary_buckets']['us_equity_sentiment']



def test_classify_event_domain_recognizes_expanded_macro_release_and_liquidity_terms():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_keyword_upgrade_macro')

    assert mod.classify_event_domain('Core PCE came in below expectations while DXY and 10Y Treasury yields fell after the release') == 'geo'
    assert mod.classify_event_domain('Initial jobless claims rose while Fed dot plot signaled fewer cuts') == 'geo'
    assert mod.classify_event_domain('Jackson Hole remarks reinforced quantitative tightening and tighter financial conditions') == 'geo'



def test_classify_event_domain_recognizes_expanded_geo_shipping_and_sanctions_terms():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_keyword_upgrade_geo')

    assert mod.classify_event_domain('Red Sea shipping disruption deepens after commercial vessel attack near Bab el-Mandeb') == 'geo'
    assert mod.classify_event_domain('Secondary sanctions and SWIFT restrictions on Russian banks tighten further') == 'geo'
    assert mod.classify_event_domain('Refinery strike raises risk of crude supply disruption and emergency SPR release') == 'geo'
    assert mod.classify_event_domain('Officials said talks will continue and pressure remains on both sides') == 'noise'



def test_classify_event_domain_and_macro_filter_upgrade_for_us_equity_proxies_and_noise_rejections():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_keyword_upgrade_equity')

    assert mod.classify_event_domain('VIX spikes as Nasdaq futures and ES1! slide before the US open') == 'geo'
    assert mod.classify_event_domain('IBIT and ETHA see strong inflows while HOOD and MARA rally with crypto beta names') == 'geo'
    assert mod.classify_event_domain('Tesla and Nvidia jump after earnings while Apple leads megacaps higher') == 'noise'

    macro_rules = {
        'macro_summary_relevance_keywords': ['vix', 'nasdaq futures', 'es1!', 'ibit', 'etha', 'hood', 'mara', 'red sea', 'secondary sanctions', 'core pce', 'jobless claims'],
        'macro_summary_exclude_keywords': ['tesla', 'nvidia', 'apple', '立即观看', '直播'],
    }
    assert mod.is_macro_summary_candidate('VIX spikes as Nasdaq futures and ES1! slide before the US open', macro_rules) is True
    assert mod.is_macro_summary_candidate('Tesla and Nvidia jump after earnings while Apple leads megacaps higher', macro_rules) is False



def test_macro_filter_rejects_chart_headlines_and_noncore_china_dragon_proxy_noise():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_keyword_upgrade_noise_refine')

    assert mod.classify_event_domain('金十图示：2026年04月23日（周四）全球股市指数-美洲市场（盘初）') == 'noise'
    assert mod.is_macro_summary_candidate(
        '金十图示：2026年04月23日（周四）全球股市指数-美洲市场（盘初）',
        {
            'macro_summary_relevance_keywords': ['盘初', '纳斯达克', '标普500'],
            'macro_summary_exclude_keywords': ['金十图示', '中国金龙指数'],
        },
    ) is False
    assert mod.is_macro_summary_candidate(
        '纳斯达克中国金龙指数跌超2%。',
        {
            'macro_summary_relevance_keywords': ['纳斯达克', '标普500', 'qqq', 'spy'],
            'macro_summary_exclude_keywords': ['中国金龙指数'],
        },
    ) is False



def test_classify_risk_state_does_not_promote_to_extreme_for_generic_geo_plus_event_plus_high_impact_count_only():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_risk_state_not_extreme_for_generic_stack')

    assert mod.classify_risk_state(
        {
            'geo_risk': 'high',
            'event_pre_release': True,
            'event_recent_release': False,
            'news_risk': 'high',
            'security_events': [],
            'fear_greed_classification': 'neutral',
            'moss_sentiment_today': 47,
        }
    ) == 'medium'



def test_merge_context_derives_news_risk_from_semantic_severity_not_source_counts():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_semantic_news_risk')
    ctx = mod.merge_context(
        raw_data={
            'jin10': {'status': 'ok', 'updated_at': '2026-04-23T11:58:00+00:00', 'data': {'macro': {'geo_risk': 'low', 'event_window': False, 'event_pre_release': False, 'event_recent_release': False, 'macro_summary': []}}},
            'blockbeats': {'status': 'ok', 'updated_at': '2026-04-23T11:55:00+00:00', 'data': {'crypto_news': {'market_bias': 'neutral', 'high_impact_events': [{'title': 'ETF inflows continue', 'impact': 'bullish', 'source': 'blockbeats'}]}, 'market_context': {}, 'macro': {}}},
            'cmc': {'status': 'ok', 'updated_at': '2026-04-23T11:54:00+00:00', 'data': {'macro': {'fear_greed_classification': 'neutral', 'fear_greed_value': 50, 'altcoin_season_classification': 'neutral', 'altcoin_season_value': 50}, 'market_context': {'market_breadth': 'mixed', 'large_cap_leadership': 'btc_leading'}, 'social': {}}},
            'moss_xsignal': {'status': 'ok', 'updated_at': '2026-04-23T11:53:00+00:00', 'data': {'macro': {'moss_sentiment_today': 50, 'moss_sentiment_bias': 'neutral'}, 'social': {'moss_available_dates': []}}},
            'okx_market': {'status': 'ok', 'updated_at': '2026-04-23T11:52:00+00:00', 'data': {'social': {}}},
            'okx_positions': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'has_positions': False, 'prioritized_symbols': [], 'live_symbols': [], 'demo_symbols': []}},
            'okx_news': {'status': 'ok', 'updated_at': '2026-04-23T11:57:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'high', 'high_impact_events': [{'title': 'ETF inflows continue', 'impact': 'bullish', 'source': 'okx_news'}]}},
            'opennews': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_bias': 'neutral', 'news_risk': 'low', 'high_impact_events': []}},
            'opentwitter': {'status': 'ok', 'updated_at': '2026-04-23T11:56:00+00:00', 'data': {'market_narrative': 'unknown', 'watch_accounts': [], 'social_risk': 'low', 'symbol_mentions': [], 'top_discussed_symbols': []}},
        },
        rules={'staleness_threshold_minutes': {}},
    )

    assert ctx['crypto_news']['news_risk'] == 'low'



def test_classify_risk_state_promotes_confirmed_geo_shock_to_extreme_when_stack_is_real():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_risk_state_geo_shock_extreme')

    assert mod.classify_risk_state(
        {
            'geo_risk': 'high',
            'geo_risk_has_shock': True,
            'event_pre_release': True,
            'event_recent_release': False,
            'news_risk': 'high',
            'security_events': [],
            'fear_greed_classification': 'fear',
            'moss_sentiment_today': 32,
        }
    ) == 'extreme'



def test_derive_news_risk_downgrades_isolated_non_systemic_project_blowup_when_no_holdings_match():
    mod = load_module(MODULE_PATH, 'context_cache_builder_under_test_isolated_project_blowup')
    ranked_events = [
        {
            'title': 'DSJEX资金盘崩盘：涉案超1.5亿美元，已冻结约4150万美元',
            'event_domains': ['regulation'],
            'event_subtypes': ['asset_freeze'],
            'market_bias': 'unknown',
            'novelty': 'new',
            'holds_match': False,
        },
        {
            'title': 'CoinShares: Global crypto ETPs saw a net inflow of $117.8 million last week',
            'event_domains': ['institutional'],
            'event_subtypes': ['etf_flow'],
            'market_bias': 'bullish',
            'novelty': 'new',
            'holds_match': False,
        },
    ]

    assert mod.derive_news_risk(ranked_events, []) == 'low'
