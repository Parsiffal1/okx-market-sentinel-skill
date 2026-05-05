from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/opennews_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('opennews_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_result_summary_uses_precise_field_names():
    mod = load_module()
    summary = mod.build_result_summary(
        items=[{'id': 1}, {'id': 2}, {'id': 3}],
        high_impact_events=[{'title': 'x'}],
        market_bias='neutral',
    )

    assert summary == {
        'raw_items': 3,
        'high_impact_events': 1,
        'market_bias': 'neutral',
    }


def test_build_search_payload_returns_global_stream_only():
    mod = load_module()

    payload = mod.build_search_payload()

    assert payload == {'limit': 20, 'page': 1}


def test_fetch_search_results_uses_single_global_payload(monkeypatch):
    mod = load_module()
    calls = []

    def fake_fetch_json(url, method='GET', payload=None, token=None):
        calls.append({'url': url, 'method': method, 'payload': payload, 'token': token})
        return {'data': [{'id': 1, 'text': 'global headline'}]}

    monkeypatch.setattr(mod, 'fetch_json', fake_fetch_json)

    items, searches = mod.fetch_search_results('token')

    assert items == [{'id': 1, 'text': 'global headline'}]
    assert searches == [{'payload': {'limit': 20, 'page': 1}, 'result': {'data': [{'id': 1, 'text': 'global headline'}]}}]
    assert calls == [{
        'url': 'https://ai.6551.io/open/news_search',
        'method': 'POST',
        'payload': {'limit': 20, 'page': 1},
        'token': 'token',
    }]
