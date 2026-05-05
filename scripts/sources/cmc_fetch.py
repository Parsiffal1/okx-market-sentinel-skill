#!/usr/bin/env python3
"""Fetch CoinMarketCap quantitative market signals for Phase3."""

from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from _common import get_env, result_error, result_ok, write_raw_cache

SOURCE = 'cmc'
BASE_URL = 'https://pro-api.coinmarketcap.com'
RAW_FILENAME = 'cmc_cache.json'
FetchFn = Callable[[str, str, dict[str, str], str], Any]
WriteCacheFn = Callable[[str, str, str, dict[str, Any], str | None], Path]


def build_request_specs() -> dict[str, dict[str, Any]]:
    return {
        'key_info': {'path': '/v1/key/info', 'params': {}},
        'global_metrics': {'path': '/v1/global-metrics/quotes/latest', 'params': {'convert': 'USD'}},
        'fear_greed': {'path': '/v3/fear-and-greed/latest', 'params': {}},
        'altcoin_season': {'path': '/v1/altcoin-season-index/latest', 'params': {}},
        'listings_latest': {'path': '/v1/cryptocurrency/listings/latest', 'params': {'start': '1', 'limit': '20', 'convert': 'USD'}},
        'quotes_latest': {'path': '/v2/cryptocurrency/quotes/latest', 'params': {'symbol': 'BTC,ETH,SOL', 'convert': 'USD'}},
        'ohlcv_latest': {'path': '/v1/cryptocurrency/ohlcv/latest', 'params': {'symbol': 'BTC,ETH,SOL', 'convert': 'USD'}},
        'price_performance': {'path': '/v2/cryptocurrency/price-performance-stats/latest', 'params': {'symbol': 'BTC,ETH,SOL', 'convert': 'USD'}},
        'trending_latest': {'path': '/v1/cryptocurrency/trending/latest', 'params': {'limit': '10'}},
        'trending_gainers_losers': {'path': '/v1/cryptocurrency/trending/gainers-losers', 'params': {'start': '1', 'limit': '10', 'time_period': '24h', 'convert': 'USD'}},
    }


def fetch_json(name: str, path: str, params: dict[str, str], api_key: str) -> Any:
    query = urllib.parse.urlencode(params or {})
    url = f'{BASE_URL}{path}' + (f'?{query}' if query else '')
    req = urllib.request.Request(url, headers={'X-CMC_PRO_API_KEY': api_key, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    status = payload.get('status', {})
    try:
        error_code = int(status.get('error_code') or 0)
    except Exception:
        error_code = -1
    if error_code != 0:
        raise RuntimeError(status.get('error_message') or f'CMC API error for {name}')
    return payload.get('data')


def classify_fear_greed(data: dict[str, Any]) -> str:
    value = int(data.get('value') or 0)
    if value <= 20:
        return 'extreme_fear'
    if value <= 44:
        return 'fear'
    if value <= 55:
        return 'neutral'
    if value <= 79:
        return 'greed'
    return 'extreme_greed'


def classify_altcoin_season(data: dict[str, Any]) -> str:
    value = int(data.get('altcoin_index') or 0)
    if value <= 25:
        return 'btc_season'
    if value >= 75:
        return 'altcoin_season'
    return 'neutral'


def classify_market_breadth(items: list[dict[str, Any]]) -> str:
    changes: list[float] = []
    for item in items or []:
        try:
            changes.append(float((((item.get('quote') or {}).get('USD') or {}).get('percent_change_24h'))))
        except Exception:
            continue
    if not changes:
        return 'unknown'
    positive_ratio = sum(1 for value in changes if value > 0) / len(changes)
    if positive_ratio >= 0.6:
        return 'broad_risk_on'
    if positive_ratio <= 0.4:
        return 'broad_risk_off'
    return 'mixed'


def classify_large_cap_leadership(quotes_latest: dict[str, Any]) -> str:
    perf: dict[str, float] = {}
    for symbol in ['BTC', 'ETH', 'SOL']:
        entries = quotes_latest.get(symbol) if isinstance(quotes_latest, dict) else None
        if not isinstance(entries, list) or not entries:
            continue
        try:
            perf[symbol] = float((((entries[0].get('quote') or {}).get('USD') or {}).get('percent_change_24h')))
        except Exception:
            continue
    if not perf:
        return 'unknown'
    winner = max(perf, key=perf.get)
    return {
        'BTC': 'btc_leading',
        'ETH': 'eth_leading',
        'SOL': 'sol_leading',
    }.get(winner, 'unknown')


def extract_trending_symbols(items: list[dict[str, Any]], limit: int = 10) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for item in items or []:
        symbol = str(item.get('symbol') or '').upper().strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
        if len(symbols) >= limit:
            break
    return symbols


def fetch_okx_instruments(inst_type: str) -> list[dict[str, Any]]:
    cmd = ['okx', '--profile', 'live', 'market', 'instruments', '--instType', inst_type, '--json']
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f'okx instruments failed: {inst_type}')
    payload = json.loads(proc.stdout)
    if isinstance(payload, dict) and 'data' in payload:
        payload = payload.get('data') or []
    return payload if isinstance(payload, list) else []


def extract_symbol_from_inst_id(inst_id: str) -> str | None:
    if not inst_id:
        return None
    base = str(inst_id).split('-', 1)[0].strip().upper()
    return base or None


def fetch_okx_tradable_symbols() -> set[str]:
    symbols: set[str] = set()
    for inst_type in ['SWAP', 'FUTURES']:
        for item in fetch_okx_instruments(inst_type):
            if str(item.get('state', '')).lower() != 'live':
                continue
            symbol = extract_symbol_from_inst_id(str(item.get('instId', '')))
            if symbol:
                symbols.add(symbol)
    return symbols


def filter_trending_symbols(symbols: list[str], tradable_symbols: set[str] | None) -> list[str]:
    if not tradable_symbols:
        return symbols
    return [symbol for symbol in symbols if symbol in tradable_symbols]


def summarize_macro(global_metrics: dict[str, Any], fear_greed: dict[str, Any], altcoin_season: dict[str, Any]) -> list[str]:
    summary: list[str] = []
    fear_value = fear_greed.get('value')
    fear_label = classify_fear_greed(fear_greed)
    if fear_value is not None:
        summary.append(f'CMC Fear & Greed {fear_value} ({fear_label})')
    alt_value = altcoin_season.get('altcoin_index')
    if alt_value is not None:
        summary.append(f'CMC Altcoin Season {alt_value} ({classify_altcoin_season(altcoin_season)})')
    btc_dom = global_metrics.get('btc_dominance')
    eth_dom = global_metrics.get('eth_dominance')
    if btc_dom is not None and eth_dom is not None:
        summary.append(f'BTC dominance {btc_dom:.2f}%, ETH dominance {eth_dom:.2f}%')
    return summary[:3]


def run_fetch(
    token: str,
    fetcher: FetchFn = fetch_json,
    write_cache: WriteCacheFn = write_raw_cache,
    tradable_symbols: set[str] | None = None,
    okx_symbol_fetcher: Callable[[], set[str]] = fetch_okx_tradable_symbols,
) -> dict[str, Any]:
    if not token:
        raise ValueError('CMC_API_KEY is required')

    payloads: dict[str, Any] = {}
    for name, spec in build_request_specs().items():
        payloads[name] = fetcher(name, spec['path'], spec['params'], token)

    listings_latest = payloads.get('listings_latest') if isinstance(payloads.get('listings_latest'), list) else []
    trending_latest = payloads.get('trending_latest') if isinstance(payloads.get('trending_latest'), list) else []
    trending_gainers_losers = payloads.get('trending_gainers_losers') if isinstance(payloads.get('trending_gainers_losers'), list) else []
    fear_greed = payloads.get('fear_greed') if isinstance(payloads.get('fear_greed'), dict) else {}
    altcoin_season = payloads.get('altcoin_season') if isinstance(payloads.get('altcoin_season'), dict) else {}
    global_metrics = payloads.get('global_metrics') if isinstance(payloads.get('global_metrics'), dict) else {}
    quotes_latest = payloads.get('quotes_latest') if isinstance(payloads.get('quotes_latest'), dict) else {}
    key_info = payloads.get('key_info') if isinstance(payloads.get('key_info'), dict) else {}
    if tradable_symbols is None:
        tradable_symbols = okx_symbol_fetcher()
    filtered_trending_symbols = filter_trending_symbols(extract_trending_symbols(trending_latest), tradable_symbols)

    data = {
        'macro': {
            'fear_greed_classification': classify_fear_greed(fear_greed),
            'fear_greed_value': fear_greed.get('value'),
            'altcoin_season_classification': classify_altcoin_season(altcoin_season),
            'altcoin_season_value': altcoin_season.get('altcoin_index'),
            'btc_dominance': global_metrics.get('btc_dominance'),
            'eth_dominance': global_metrics.get('eth_dominance'),
            'total_market_cap_change_24h': (((global_metrics.get('quote') or {}).get('USD') or {}).get('total_market_cap_yesterday_percentage_change')),
            'total_volume_change_24h': (((global_metrics.get('quote') or {}).get('USD') or {}).get('total_volume_24h_yesterday_percentage_change')),
            'macro_summary': summarize_macro(global_metrics, fear_greed, altcoin_season),
        },
        'market_context': {
            'market_breadth': classify_market_breadth(listings_latest),
            'large_cap_leadership': classify_large_cap_leadership(quotes_latest),
        },
        'social': {
            'cmc_trending_symbols': filtered_trending_symbols,
        },
        'diagnostics': {
            'rate_limit_minute': (((key_info.get('plan') or {}).get('rate_limit_minute'))),
            'credits_left_month': ((((key_info.get('usage') or {}).get('current_month') or {}).get('credits_left'))),
        },
        'raw': payloads,
    }

    path = write_cache(RAW_FILENAME, SOURCE, 'ok', data)
    return {'status': 'ok', 'path': path, 'data': data}


def main() -> None:
    token = get_env('CMC_API_KEY')
    try:
        result = run_fetch(token)
        result_ok(result['path'], SOURCE, {
            'status': result['status'],
            'macro': result['data']['macro'],
            'market_breadth': result['data']['market_context']['market_breadth'],
            'cmc_trending_symbols': len(result['data']['social']['cmc_trending_symbols']),
        })
    except Exception as exc:
        path = write_raw_cache(RAW_FILENAME, SOURCE, 'error', {}, error=str(exc))
        result_error(SOURCE, f'{exc} (cache written: {path})')


if __name__ == '__main__':
    main()
