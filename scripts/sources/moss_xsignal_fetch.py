#!/usr/bin/env python3
"""Fetch Moss X Signal sentiment data for Phase3."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from _common import result_error, result_ok, write_raw_cache

SOURCE = 'moss_xsignal'
RAW_FILENAME = 'moss_xsignal_cache.json'
BASE_URL = 'https://ai.moss.site/api/v1'
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json,text/plain,*/*',
    'Referer': 'https://moss.site/sentiment',
    'Origin': 'https://moss.site',
}


def fetch_json(path: str) -> Any:
    req = urllib.request.Request(f'{BASE_URL}{path}', headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def sentiment_bias(value: int | float | None) -> str:
    if value is None:
        return 'unknown'
    try:
        value = float(value)
    except Exception:
        return 'unknown'
    if value >= 65:
        return 'bullish'
    if value >= 55:
        return 'slightly_bullish'
    if value >= 45:
        return 'neutral'
    if value >= 35:
        return 'slightly_bearish'
    return 'bearish'


def run_fetch(write_cache=write_raw_cache) -> dict[str, Any]:
    global_list = fetch_json('/sentiment/global/list')
    available_dates = fetch_json('/sentiment-edge/available-dates')

    history = (((global_list or {}).get('data') or {}).get('sentiment_history') or [])
    latest = history[0] if history else {}
    sentiment_value = latest.get('sentiment')
    data = {
        'macro': {
            'moss_sentiment_today': sentiment_value,
            'moss_sentiment_pub': latest.get('pub_sentiment'),
            'moss_sentiment_date': latest.get('date'),
            'moss_btc_price': latest.get('btc_price'),
            'moss_sentiment_bias': sentiment_bias(sentiment_value),
        },
        'social': {
            'moss_available_dates': (((available_dates or {}).get('data') or {}).get('dates') or [])[:30],
        },
        'raw': {
            'global_list': global_list,
            'available_dates': available_dates,
        },
    }
    path = write_cache(RAW_FILENAME, SOURCE, 'ok', data)
    return {'status': 'ok', 'path': path, 'data': data}


def main() -> None:
    try:
        result = run_fetch()
        result_ok(result['path'], SOURCE, {
            'status': result['status'],
            'moss_sentiment_today': result['data']['macro']['moss_sentiment_today'],
            'moss_sentiment_bias': result['data']['macro']['moss_sentiment_bias'],
            'available_dates': len(result['data']['social']['moss_available_dates']),
        })
    except Exception as exc:
        path = write_raw_cache(RAW_FILENAME, SOURCE, 'error', {}, error=str(exc))
        result_error(SOURCE, f'{exc} (cache written: {path})')


if __name__ == '__main__':
    main()
