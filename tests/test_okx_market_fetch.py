from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/okx_market_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('okx_market_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_classify_oi_price_quadrant_maps_four_quadrants():
    mod = load_module()

    assert mod.classify_oi_price_quadrant(12.0, 3.5) == 'oi_up_price_up'
    assert mod.classify_oi_price_quadrant(8.0, -2.1) == 'oi_up_price_down'
    assert mod.classify_oi_price_quadrant(-4.0, 1.8) == 'oi_down_price_up'
    assert mod.classify_oi_price_quadrant(-7.0, -5.2) == 'oi_down_price_down'


def test_run_fetch_supports_multiple_contract_types_not_only_swaps(tmp_path):
    mod = load_module()
    written = {}

    def fake_runner(command: list[str]):
        joined = ' '.join(command)
        if '--instType SWAP' in joined and 'sortBy chg24hPct' in joined:
            return [{'instId': 'TON-USDT-SWAP', 'last': '1.8', 'chg24hPct': '36.36', 'oiUsd': '3581058769.14', 'volUsd24h': '6128654487.55', 'fundingRate': '-0.0001238'}]
        if '--instType FUTURES' in joined and 'sortBy chg24hPct' in joined:
            return [{'instId': 'GC-USD-240628', 'last': '2380', 'chg24hPct': '4.5', 'oiUsd': '125000000', 'volUsd24h': '89000000', 'fundingRate': '0'}]
        if '--instType SWAP' in joined and 'sortBy oiUsd' in joined:
            return [{'instId': 'ETH-USDT-SWAP', 'last': '2376.85', 'chg24hPct': '1.59', 'oiUsd': '2903803937838.57', 'volUsd24h': '276578822819.25', 'fundingRate': '0.00005824'}]
        if '--instType FUTURES' in joined and 'sortBy oiUsd' in joined:
            return [{'instId': 'CL-USD-240628', 'last': '78.4', 'chg24hPct': '2.1', 'oiUsd': '220000000', 'volUsd24h': '91000000', 'fundingRate': '0'}]
        if '--instType SWAP' in joined and 'oi-change' in joined:
            return [{'instId': 'TSLA-USDT-SWAP', 'last': '394.21', 'oiUsd': '51841475.40', 'prevOiUsd': '328653.45', 'oiDeltaUsd': '51512821.95', 'oiDeltaPct': '15673.9028', 'pxChgPct': '1.1054', 'fundingRate': '0.00061165', 'volUsd24h': '132314714.00'}]
        if '--instType FUTURES' in joined and 'oi-change' in joined:
            return [{'instId': 'GC-USD-240628', 'last': '2380', 'oiUsd': '125000000', 'prevOiUsd': '118000000', 'oiDeltaUsd': '7000000', 'oiDeltaPct': '5.9', 'pxChgPct': '4.5', 'fundingRate': '0', 'volUsd24h': '89000000'}]
        raise AssertionError(joined)

    def fake_write_raw_cache(filename: str, source: str, status: str, data: dict, error: str | None = None):
        written.update({'filename': filename, 'source': source, 'status': status, 'data': data, 'error': error})
        path = tmp_path / filename
        path.write_text('ok', encoding='utf-8')
        return path

    result = mod.run_fetch(runner=fake_runner, write_cache=fake_write_raw_cache)

    assert result['status'] == 'ok'
    assert written['data']['social']['okx_gainer_symbols'] == ['TON', 'GC']
    assert written['data']['social']['okx_top_oi_symbols'] == ['ETH', 'CL']
    assert written['data']['social']['okx_oi_change_symbols'] == ['TSLA', 'GC']



def test_run_fetch_keeps_all_okx_tradable_contract_types_including_stock_tokens(tmp_path):
    mod = load_module()
    written = {}

    gainer_rows = [
        {'instId': 'AAPL-USDT-SWAP', 'last': '757.713', 'chg24hPct': '119.49', 'oiUsd': '9324066895.04', 'volUsd24h': '375213749.29', 'fundingRate': '0.00005'},
        {'instId': 'TON-USDT-SWAP', 'last': '1.8', 'chg24hPct': '36.36', 'oiUsd': '3581058769.14', 'volUsd24h': '6128654487.55', 'fundingRate': '-0.0001238'},
    ]
    oi_rows = [
        {'instId': 'ETH-USDT-SWAP', 'last': '2376.85', 'chg24hPct': '1.59', 'oiUsd': '2903803937838.57', 'volUsd24h': '276578822819.25', 'fundingRate': '0.00005824'},
        {'instId': 'AAPL-USDT-SWAP', 'last': '757.713', 'chg24hPct': '119.49', 'oiUsd': '9324066895.04', 'volUsd24h': '375213749.29', 'fundingRate': '0.00005'},
    ]
    oi_change_rows = [
        {'instId': 'TSLA-USDT-SWAP', 'last': '394.21', 'oiUsd': '51841475.40', 'prevOiUsd': '328653.45', 'oiDeltaUsd': '51512821.95', 'oiDeltaPct': '15673.9028', 'pxChgPct': '1.1054', 'fundingRate': '0.00061165', 'volUsd24h': '132314714.00'},
        {'instId': 'LINK-USDT-SWAP', 'last': '9.674', 'oiUsd': '217787491.78', 'prevOiUsd': '95838386.80', 'oiDeltaUsd': '121949104.98', 'oiDeltaPct': '127.2445', 'pxChgPct': '2.3812', 'fundingRate': '0.0001', 'volUsd24h': '5512825773.31'},
    ]

    def fake_runner(command: list[str]):
        joined = ' '.join(command)
        if 'sortBy chg24hPct' in joined:
            return gainer_rows
        if 'sortBy oiUsd' in joined:
            return oi_rows
        if 'oi-change' in joined:
            return oi_change_rows
        raise AssertionError(joined)

    def fake_write_raw_cache(filename: str, source: str, status: str, data: dict, error: str | None = None):
        written.update({'filename': filename, 'source': source, 'status': status, 'data': data, 'error': error})
        path = tmp_path / filename
        path.write_text('ok', encoding='utf-8')
        return path

    result = mod.run_fetch(runner=fake_runner, write_cache=fake_write_raw_cache)

    assert result['status'] == 'ok'
    assert written['data']['social']['okx_gainer_symbols'] == ['AAPL', 'TON']
    assert written['data']['social']['okx_top_oi_symbols'] == ['ETH', 'AAPL']
    assert written['data']['social']['okx_oi_change_symbols'] == ['TSLA', 'LINK']
    assert written['data']['social']['okx_oi_change'][0]['quadrant'] == 'oi_up_price_up'



def test_run_fetch_writes_filtered_okx_market_cache(tmp_path):
    mod = load_module()
    written = {}

    stock_token_rows = [
        {'instId': 'AAPL-USDT-SWAP', 'ctValCcy': 'AAPL'},
        {'instId': 'TSLA-USDT-SWAP', 'ctValCcy': 'TSLA'},
    ]
    gainer_rows = [
        {'instId': 'AAPL-USDT-SWAP', 'last': '100', 'chg24hPct': '15', 'oiUsd': '1000', 'volUsd24h': '5000', 'fundingRate': '0.0001'},
        {'instId': 'TON-USDT-SWAP', 'last': '1.8', 'chg24hPct': '36.36', 'oiUsd': '3581058769.14', 'volUsd24h': '6128654487.55', 'fundingRate': '-0.0001238'},
    ]
    oi_rows = [
        {'instId': 'ETH-USDT-SWAP', 'last': '2376.85', 'chg24hPct': '1.59', 'oiUsd': '2903803937838.57', 'volUsd24h': '276578822819.25', 'fundingRate': '0.00005824'},
    ]
    oi_change_rows = [
        {'instId': 'TSLA-USDT-SWAP', 'last': '394.21', 'oiUsd': '51841475.40', 'prevOiUsd': '328653.45', 'oiDeltaUsd': '51512821.95', 'oiDeltaPct': '15673.9028', 'pxChgPct': '1.1054', 'fundingRate': '0.00061165', 'volUsd24h': '132314714.00'},
        {'instId': 'LINK-USDT-SWAP', 'last': '9.674', 'oiUsd': '217787491.78', 'prevOiUsd': '95838386.80', 'oiDeltaUsd': '121949104.98', 'oiDeltaPct': '127.2445', 'pxChgPct': '2.3812', 'fundingRate': '0.0001', 'volUsd24h': '5512825773.31'},
    ]

    def fake_runner(command: list[str]):
        joined = ' '.join(command)
        if 'stock-tokens' in joined:
            return stock_token_rows
        if 'sortBy chg24hPct' in joined:
            return gainer_rows
        if 'sortBy oiUsd' in joined:
            return oi_rows
        if 'oi-change' in joined:
            return oi_change_rows
        raise AssertionError(joined)

    def fake_write_raw_cache(filename: str, source: str, status: str, data: dict, error: str | None = None):
        written.update({'filename': filename, 'source': source, 'status': status, 'data': data, 'error': error})
        path = tmp_path / filename
        path.write_text('ok', encoding='utf-8')
        return path

    result = mod.run_fetch(runner=fake_runner, write_cache=fake_write_raw_cache)

    assert result['status'] == 'ok'
    assert written['source'] == 'okx_market'
    assert written['status'] == 'ok'
    assert written['data']['social']['okx_gainer_symbols'] == ['AAPL', 'TON']
    assert written['data']['social']['okx_top_oi_symbols'] == ['ETH']
    assert written['data']['social']['okx_oi_change_symbols'] == ['TSLA', 'LINK']
    assert written['data']['social']['okx_oi_change'][0]['quadrant'] == 'oi_up_price_up'
