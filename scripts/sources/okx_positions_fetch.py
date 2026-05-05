#!/usr/bin/env python3
"""Fetch OKX live/demo positions and normalize them into Phase3 holdings data."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from _common import result_error, result_ok, write_raw_cache

SOURCE = 'okx_positions'
RAW_FILENAME = 'okx_positions_cache.json'
PROFILES = {
    'live': {'profile': 'live', 'mode': 'live'},
    'demo': {'profile': 'demo', 'mode': 'demo'},
}


def run_okx_json(args: list[str], profile: str) -> Any:
    cmd = ['okx', '--profile', profile, *args, '--json']
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"command failed: {' '.join(cmd)}")
    return json.loads(proc.stdout)


def extract_symbol_from_inst_id(inst_id: str) -> str | None:
    if not inst_id:
        return None
    base = str(inst_id).split('-', 1)[0].strip().upper()
    return base or None


def sanitize_position(item: dict[str, Any]) -> dict[str, Any]:
    return {
        'instId': item.get('instId'),
        'instType': item.get('instType'),
        'posSide': item.get('posSide'),
        'pos': item.get('pos'),
        'notionalUsd': item.get('notionalUsd'),
        'avgPx': item.get('avgPx'),
        'markPx': item.get('markPx'),
        'mgnMode': item.get('mgnMode'),
        'lever': item.get('lever'),
        'symbol': extract_symbol_from_inst_id(str(item.get('instId', ''))),
    }


def fetch_positions(profile: str) -> list[dict[str, Any]]:
    payload = run_okx_json(['account', 'positions'], profile=profile)
    if isinstance(payload, list):
        return [sanitize_position(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get('data'), list):
        return [sanitize_position(item) for item in payload.get('data', []) if isinstance(item, dict)]
    return []


def symbols_from_positions(positions: list[dict[str, Any]]) -> list[str]:
    symbols: list[str] = []
    seen: set[str] = set()
    for item in positions:
        symbol = str(item.get('symbol') or extract_symbol_from_inst_id(str(item.get('instId', ''))) or '').strip().upper()
        if symbol and symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)
    return symbols


def build_holdings_payload(live_positions: list[dict[str, Any]], demo_positions: list[dict[str, Any]]) -> dict[str, Any]:
    live_symbols = symbols_from_positions(live_positions)
    demo_symbols = symbols_from_positions(demo_positions)
    prioritized_symbols = live_symbols + [symbol for symbol in demo_symbols if symbol not in set(live_symbols)]
    return {
        'has_positions': bool(live_positions or demo_positions),
        'prioritized_symbols': prioritized_symbols,
        'accounts': {
            'live': {
                'symbols': live_symbols,
                'positions': live_positions,
            },
            'demo': {
                'symbols': demo_symbols,
                'positions': demo_positions,
            },
        },
    }


def get_holdings_payload() -> dict[str, Any]:
    errors: dict[str, str] = {}
    positions_by_account: dict[str, list[dict[str, Any]]] = {'live': [], 'demo': []}
    for account_name, meta in PROFILES.items():
        try:
            positions_by_account[account_name] = fetch_positions(meta['profile'])
        except Exception as exc:
            errors[account_name] = str(exc)
    payload = build_holdings_payload(positions_by_account['live'], positions_by_account['demo'])
    if errors:
        payload['errors'] = errors
    return payload


def main() -> None:
    try:
        data = get_holdings_payload()
        path = write_raw_cache(RAW_FILENAME, SOURCE, 'ok', data)
        result_ok(path, SOURCE, {
            'has_positions': data['has_positions'],
            'live_positions': len(data['accounts']['live']['positions']),
            'demo_positions': len(data['accounts']['demo']['positions']),
            'prioritized_symbols': data['prioritized_symbols'],
        })
    except Exception as exc:
        path = write_raw_cache(RAW_FILENAME, SOURCE, 'error', {}, error=str(exc))
        result_error(SOURCE, f'failed to fetch OKX positions, cache written to {path}: {exc}')


if __name__ == '__main__':
    main()
