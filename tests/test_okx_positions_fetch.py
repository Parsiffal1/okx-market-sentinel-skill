from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/okx_positions_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('okx_positions_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_holdings_payload_prioritizes_live_then_demo_symbols():
    mod = load_module()

    payload = mod.build_holdings_payload(
        live_positions=[
            {'instId': 'BTC-USDT-SWAP', 'instType': 'SWAP', 'posSide': 'short', 'pos': '3.79', 'notionalUsd': '2950'},
        ],
        demo_positions=[
            {'instId': 'RAVE-USDT-SWAP', 'instType': 'SWAP', 'posSide': 'short', 'pos': '196', 'notionalUsd': '998'},
            {'instId': 'BTC-USDT-SWAP', 'instType': 'SWAP', 'posSide': 'short', 'pos': '1', 'notionalUsd': '100'},
        ],
    )

    assert payload['has_positions'] is True
    assert payload['prioritized_symbols'] == ['BTC', 'RAVE']
    assert payload['accounts']['live']['symbols'] == ['BTC']
    assert payload['accounts']['demo']['symbols'] == ['RAVE', 'BTC']
