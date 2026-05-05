from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/opentwitter_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('opentwitter_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extract_symbols_from_text_supports_aliases_case_and_meme_tokens():
    mod = load_module()
    rules = {
        'major_aliases': {
            'BTC': ['BTC', '大饼'],
            'ETH': ['ETH', '二饼', '以太', '姨太'],
            'SOL': ['SOL'],
        },
        'symbol_ignore_tokens': ['CRYPTO'],
    }

    symbols = mod.extract_symbols_from_text(
        '大饼今天很强，eth和姨太都不错，sol 也稳，顺便看看chip 和 $wld，#crypto。',
        rules,
    )

    assert symbols == ['BTC', 'ETH', 'SOL', 'CHIP', 'WLD']


def test_build_symbol_mentions_aggregates_heat_and_categories():
    mod = load_module()
    rules = {
        'major_aliases': {
            'BTC': ['BTC', '大饼'],
            'ETH': ['ETH', '以太', '姨太'],
            'SOL': ['SOL'],
        },
        'symbol_ignore_tokens': ['CRYPTO'],
        'heat_weights': {
            'view_count': 1,
            'favorite_count': 20,
            'reply_count': 30,
        },
    }
    all_items = [
        {
            'text': '大饼继续强，BTC maybe go higher, chip 也有人聊',
            'viewCount': 1000,
            'favoriteCount': 10,
            'replyCount': 2,
            'userScreenName': 'alpha',
        },
        {
            'text': 'sol 和 CHIP 今天继续热，姨太也有表现',
            'viewCount': 500,
            'favoriteCount': 5,
            'replyCount': 1,
            'userScreenName': 'beta',
        },
    ]

    mentions = mod.build_symbol_mentions(all_items, rules)

    assert mentions[0]['symbol'] == 'CHIP'
    assert mentions[0]['category'] == 'meme'
    assert mentions[0]['mention_count'] == 2
    assert mentions[0]['unique_accounts'] == 2
    assert mentions[0]['weighted_heat'] == 1890

    btc = next(item for item in mentions if item['symbol'] == 'BTC')
    assert btc['category'] == 'major'
    assert btc['mention_count'] == 1
    assert btc['weighted_heat'] == 1260

    eth = next(item for item in mentions if item['symbol'] == 'ETH')
    assert eth['mention_count'] == 1

    sol = next(item for item in mentions if item['symbol'] == 'SOL')
    assert sol['mention_count'] == 1


def test_filter_symbol_mentions_by_okx_tradable_symbols():
    mod = load_module()
    mentions = [
        {'symbol': 'BTC', 'category': 'major', 'mention_count': 3, 'unique_accounts': 2, 'weighted_heat': 1000},
        {'symbol': 'CHIP', 'category': 'meme', 'mention_count': 2, 'unique_accounts': 2, 'weighted_heat': 900},
        {'symbol': 'UNKNOWN', 'category': 'meme', 'mention_count': 5, 'unique_accounts': 4, 'weighted_heat': 5000},
    ]

    filtered = mod.filter_symbol_mentions_by_okx_symbols(mentions, {'BTC', 'CHIP'})

    assert [item['symbol'] for item in filtered] == ['BTC', 'CHIP']


def test_build_account_results_trims_to_supported_interaction_fields():
    mod = load_module()
    raw = {
        'thankUcrypto': {
            'data': [
                {
                    'id': '1',
                    'text': '大饼和sol都在看，chip也有热度',
                    'createdAt': 'Thu Apr 23 02:56:22 +0000 2026',
                    'viewCount': 100,
                    'favoriteCount': 2,
                    'replyCount': 1,
                    'retweetCount': 9,
                    'quoteCount': 3,
                    'userScreenName': 'thankUcrypto',
                    'userFollowers': 1000,
                    'userName': 'allincrypto',
                    'userIdStr': '123',
                }
            ]
        }
    }

    account_results, all_items = mod.build_account_results(raw)

    assert account_results[0]['username'] == 'thankUcrypto'
    assert 'bias' not in account_results[0]
    assert all_items[0]['viewCount'] == 100
    assert all_items[0]['favoriteCount'] == 2
    assert all_items[0]['replyCount'] == 1
    assert 'retweetCount' not in all_items[0]
    assert 'quoteCount' not in all_items[0]


def test_build_result_contains_discussion_fields_from_symbol_mentions():
    mod = load_module()
    rules = {
        'major_aliases': {
            'BTC': ['BTC', '大饼'],
            'ETH': ['ETH', '以太', '姨太'],
            'SOL': ['SOL'],
        },
        'symbol_ignore_tokens': [],
        'heat_weights': {
            'view_count': 1,
            'favorite_count': 20,
            'reply_count': 30,
        },
    }
    raw = {
        'thankUcrypto': {
            'data': [
                {
                    'id': '1',
                    'text': '大饼和sol都在看，chip也有热度',
                    'viewCount': 100,
                    'favoriteCount': 2,
                    'replyCount': 1,
                    'userScreenName': 'thankUcrypto',
                    'userFollowers': 1000,
                }
            ]
        }
    }

    account_results, all_items = mod.build_account_results(raw)
    mentions = mod.build_symbol_mentions(all_items, rules)

    payload = mod.build_social_payload(raw=raw, account_results=account_results, all_items=all_items, errors={}, rules=rules, okx_symbols={'BTC', 'CHIP', 'SOL'})

    assert payload['watch_accounts'][0]['username'] == 'thankUcrypto'
    assert 'bias' not in payload['watch_accounts'][0]
    assert payload['top_discussed_symbols'] == ['BTC', 'CHIP', 'SOL']
    assert payload['symbol_mentions'] == mentions
