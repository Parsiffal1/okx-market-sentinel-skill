from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/cmc_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('cmc_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_request_specs_uses_verified_supported_endpoints_only():
    mod = load_module()

    specs = mod.build_request_specs()

    assert list(specs) == [
        'key_info',
        'global_metrics',
        'fear_greed',
        'altcoin_season',
        'listings_latest',
        'quotes_latest',
        'ohlcv_latest',
        'price_performance',
        'trending_latest',
        'trending_gainers_losers',
    ]
    assert specs['global_metrics']['path'] == '/v1/global-metrics/quotes/latest'
    assert specs['fear_greed']['path'] == '/v3/fear-and-greed/latest'
    assert specs['altcoin_season']['path'] == '/v1/altcoin-season-index/latest'
    assert specs['trending_latest']['path'] == '/v1/cryptocurrency/trending/latest'


def test_classification_helpers_normalize_cmc_signals():
    mod = load_module()

    assert mod.classify_fear_greed({'value': 18}) == 'extreme_fear'
    assert mod.classify_fear_greed({'value': 41}) == 'fear'
    assert mod.classify_fear_greed({'value': 55}) == 'neutral'
    assert mod.classify_fear_greed({'value': 69}) == 'greed'
    assert mod.classify_fear_greed({'value': 88}) == 'extreme_greed'

    assert mod.classify_altcoin_season({'altcoin_index': 18}) == 'btc_season'
    assert mod.classify_altcoin_season({'altcoin_index': 48}) == 'neutral'
    assert mod.classify_altcoin_season({'altcoin_index': 82}) == 'altcoin_season'

    assert mod.classify_market_breadth([
        {'quote': {'USD': {'percent_change_24h': 6.1}}},
        {'quote': {'USD': {'percent_change_24h': 2.0}}},
        {'quote': {'USD': {'percent_change_24h': 1.0}}},
        {'quote': {'USD': {'percent_change_24h': -0.5}}},
        {'quote': {'USD': {'percent_change_24h': 4.2}}},
    ]) == 'broad_risk_on'
    assert mod.classify_market_breadth([
        {'quote': {'USD': {'percent_change_24h': -6.1}}},
        {'quote': {'USD': {'percent_change_24h': -2.0}}},
        {'quote': {'USD': {'percent_change_24h': -1.0}}},
        {'quote': {'USD': {'percent_change_24h': 0.5}}},
        {'quote': {'USD': {'percent_change_24h': -4.2}}},
    ]) == 'broad_risk_off'


def test_run_fetch_writes_compact_ok_cache(tmp_path):
    mod = load_module()
    written = {}

    fake_payloads = {
        'key_info': {'plan': {'credit_limit_monthly': 450000, 'rate_limit_minute': 600}, 'usage': {'current_month': {'credits_left': 449000}}},
        'global_metrics': {
            'btc_dominance': 60.1,
            'eth_dominance': 10.7,
            'quote': {'USD': {'total_market_cap_yesterday_percentage_change': -1.8, 'total_volume_24h_yesterday_percentage_change': 7.2}},
        },
        'fear_greed': {'value': 32, 'value_classification': 'Fear'},
        'altcoin_season': {'altcoin_index': 22},
        'listings_latest': [
            {'name': 'Bitcoin', 'symbol': 'BTC', 'quote': {'USD': {'percent_change_24h': -1.2, 'market_cap_dominance': 60.1}}},
            {'name': 'Ethereum', 'symbol': 'ETH', 'quote': {'USD': {'percent_change_24h': -3.4, 'market_cap_dominance': 10.7}}},
            {'name': 'Solana', 'symbol': 'SOL', 'quote': {'USD': {'percent_change_24h': 2.4, 'market_cap_dominance': 3.1}}},
        ],
        'quotes_latest': {'BTC': [{'quote': {'USD': {'price': 78000}}}]},
        'ohlcv_latest': {'BTC': [{'quote': {'USD': {'close': 78000}}}]},
        'price_performance': {'BTC': [{'periods': {'24h': {'quote': {'USD': {'percent_change': -1.2}}}}}]},
        'trending_latest': [
            {'name': 'Hyperliquid', 'symbol': 'HYPE'},
            {'name': 'Fartcoin', 'symbol': 'FARTCOIN'},
        ],
        'trending_gainers_losers': [
            {'name': 'Hyperliquid', 'symbol': 'HYPE', 'quote': {'USD': {'percent_change_24h': 12.5}}},
        ],
    }

    def fake_fetch(name: str, path: str, params: dict[str, str], api_key: str):
        assert api_key == 'cmc-token'
        return fake_payloads[name]

    def fake_write_raw_cache(filename: str, source: str, status: str, data: dict, error: str | None = None):
        written.update({'filename': filename, 'source': source, 'status': status, 'data': data, 'error': error})
        path = tmp_path / filename
        path.write_text('ok', encoding='utf-8')
        return path

    result = mod.run_fetch(token='cmc-token', fetcher=fake_fetch, write_cache=fake_write_raw_cache, tradable_symbols={'HYPE'})

    assert result['status'] == 'ok'
    assert written['source'] == 'cmc'
    assert written['status'] == 'ok'
    assert written['data']['macro']['fear_greed_classification'] == 'fear'
    assert written['data']['macro']['altcoin_season_classification'] == 'btc_season'
    assert written['data']['market_context']['market_breadth'] == 'broad_risk_off'
    assert 'top_movers' not in written['data']['market_context']
    assert written['data']['social']['cmc_trending_symbols'] == ['HYPE']


def test_run_fetch_requires_token():
    mod = load_module()

    try:
        mod.run_fetch(token='')
    except ValueError as exc:
        assert 'CMC_API_KEY is required' in str(exc)
    else:
        raise AssertionError('expected ValueError for missing token')
