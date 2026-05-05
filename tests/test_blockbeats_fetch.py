from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/blockbeats_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('blockbeats_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_newsflash_endpoint_requests_20_items_per_run(monkeypatch):
    mod = load_module()
    calls = []

    def fake_fetch_json(path: str, params: dict[str, str] | None = None, api_key: str = ''):
        calls.append({'path': path, 'params': params, 'api_key': api_key})
        return []

    monkeypatch.setattr(mod, 'get_env', lambda _: 'test-key')
    monkeypatch.setattr(mod, 'fetch_json', fake_fetch_json)
    monkeypatch.setattr(mod, 'write_raw_cache', lambda *args, **kwargs: Path('/tmp/blockbeats_cache.json'))
    monkeypatch.setattr(mod, 'result_ok', lambda *args, **kwargs: None)
    monkeypatch.setattr(mod, 'result_error', lambda *args, **kwargs: None)

    mod.main()

    newsflash_call = next(call for call in calls if call['path'] == '/v1/newsflash/important')
    assert newsflash_call['params'] == {'page': '1', 'size': '20', 'lang': 'cn'}
