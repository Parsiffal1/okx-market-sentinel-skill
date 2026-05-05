#!/usr/bin/env python3
"""Fetch OKX market-screen signals for Phase3 hot-symbol ranking.

Collects three exchange-native views:
- top 24h gainers
- top open-interest contracts
- largest OI changes with price/OI quadrant labels

The goal is not trade execution. This source only provides ranking inputs for the
Phase3 hot-symbol layer.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from _common import result_error, result_ok, write_raw_cache

SOURCE = 'okx_market'
RAW_FILENAME = 'okx_market_cache.json'
RunCmdFn = Callable[[list[str]], list[dict[str, Any]]]
WriteCacheFn = Callable[[str, str, str, dict[str, Any], str | None], Path]


def parse_cli_json(stdout: str) -> Any:
    text = str(stdout or '')
    positions = [index for index in [text.find('['), text.find('{')] if index >= 0]
    if not positions:
        raise ValueError('no JSON payload found in OKX CLI output')
    return json.loads(text[min(positions):])


def run_okx_json(command: list[str]) -> list[dict[str, Any]]:
    proc = subprocess.run(command, capture_output=True, text=True, timeout=90)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f'command failed: {command}')
    payload = parse_cli_json(proc.stdout)
    if isinstance(payload, dict) and 'data' in payload:
        payload = payload.get('data') or []
    if isinstance(payload, list) and payload and isinstance(payload[0], dict) and 'rows' in payload[0]:
        return payload[0].get('rows') or []
    return payload if isinstance(payload, list) else []


def symbol_from_inst_id(inst_id: str) -> str | None:
    value = str(inst_id or '').strip().upper()
    if not value:
        return None
    return value.split('-', 1)[0] or None


def collect_market_rows(
    runner: RunCmdFn,
    command_builder: Callable[[str], list[str]],
    inst_types: tuple[str, ...] = ('SWAP', 'FUTURES'),
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for inst_type in inst_types:
        rows.extend(runner(command_builder(inst_type)) or [])
    return rows


def classify_oi_price_quadrant(oi_delta_pct: float, price_change_pct: float) -> str:
    if oi_delta_pct >= 0 and price_change_pct >= 0:
        return 'oi_up_price_up'
    if oi_delta_pct >= 0 and price_change_pct < 0:
        return 'oi_up_price_down'
    if oi_delta_pct < 0 and price_change_pct >= 0:
        return 'oi_down_price_up'
    return 'oi_down_price_down'


def normalize_rank_rows(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in rows or []:
        symbol = symbol_from_inst_id(str(item.get('instId') or ''))
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        result.append(
            {
                'symbol': symbol,
                'instId': str(item.get('instId') or ''),
                'last': float(item.get('last') or 0),
                'chg24hPct': float(item.get('chg24hPct') or 0),
                'oiUsd': float(item.get('oiUsd') or 0),
                'volUsd24h': float(item.get('volUsd24h') or 0),
                'fundingRate': float(item.get('fundingRate') or 0),
                'rank': len(result) + 1,
            }
        )
        if len(result) >= limit:
            break
    return result


def normalize_oi_change_rows(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in rows or []:
        symbol = symbol_from_inst_id(str(item.get('instId') or ''))
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        oi_delta_pct = float(item.get('oiDeltaPct') or 0)
        px_chg_pct = float(item.get('pxChgPct') or 0)
        result.append(
            {
                'symbol': symbol,
                'instId': str(item.get('instId') or ''),
                'last': float(item.get('last') or 0),
                'oiUsd': float(item.get('oiUsd') or 0),
                'prevOiUsd': float(item.get('prevOiUsd') or 0),
                'oiDeltaUsd': float(item.get('oiDeltaUsd') or 0),
                'oiDeltaPct': oi_delta_pct,
                'pxChgPct': px_chg_pct,
                'fundingRate': float(item.get('fundingRate') or 0),
                'volUsd24h': float(item.get('volUsd24h') or 0),
                'quadrant': classify_oi_price_quadrant(oi_delta_pct, px_chg_pct),
                'rank': len(result) + 1,
            }
        )
        if len(result) >= limit:
            break
    return result


def run_fetch(
    runner: RunCmdFn = run_okx_json,
    write_cache: WriteCacheFn = write_raw_cache,
) -> dict[str, Any]:
    top_gainers = normalize_rank_rows(
        collect_market_rows(
            runner,
            lambda inst_type: ['okx', 'market', 'filter', '--instType', inst_type, '--sortBy', 'chg24hPct', '--sortOrder', 'desc', '--limit', '30', '--json'],
        )
    )
    top_oi = normalize_rank_rows(
        collect_market_rows(
            runner,
            lambda inst_type: ['okx', 'market', 'filter', '--instType', inst_type, '--sortBy', 'oiUsd', '--sortOrder', 'desc', '--limit', '30', '--json'],
        )
    )
    oi_change = normalize_oi_change_rows(
        collect_market_rows(
            runner,
            lambda inst_type: ['okx', 'market', 'oi-change', '--instType', inst_type, '--bar', '4H', '--limit', '30', '--json'],
        )
    )

    data = {
        'social': {
            'okx_top_gainers': top_gainers,
            'okx_top_oi': top_oi,
            'okx_oi_change': oi_change,
            'okx_gainer_symbols': [item['symbol'] for item in top_gainers],
            'okx_top_oi_symbols': [item['symbol'] for item in top_oi],
            'okx_oi_change_symbols': [item['symbol'] for item in oi_change],
        }
    }
    path = write_cache(RAW_FILENAME, SOURCE, 'ok', data)
    return {'status': 'ok', 'path': path, 'data': data}


def main() -> None:
    try:
        result = run_fetch()
        result_ok(
            result['path'],
            SOURCE,
            {
                'status': result['status'],
                'okx_top_gainers': len(result['data']['social']['okx_top_gainers']),
                'okx_top_oi': len(result['data']['social']['okx_top_oi']),
                'okx_oi_change': len(result['data']['social']['okx_oi_change']),
            },
        )
    except Exception as exc:
        path = write_raw_cache(RAW_FILENAME, SOURCE, 'error', {}, error=str(exc))
        result_error(SOURCE, f'{exc} (cache written: {path})')


if __name__ == '__main__':
    main()
