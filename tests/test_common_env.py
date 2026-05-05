from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/_common.py"


def load_module():
    spec = importlib.util.spec_from_file_location('common_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_env_file_resolves_variable_references(tmp_path, monkeypatch):
    mod = load_module()
    env_file = tmp_path / 'test.env'
    env_file.write_text(
        'OPENNEWS_TOKEN=real-token\n'
        'TWITTER_TOKEN="$OPENNEWS_TOKEN"\n'
        'OPEN_TOKEN=${OPENNEWS_TOKEN}\n',
        encoding='utf-8',
    )
    monkeypatch.setattr(mod, 'ENV_FILES', [env_file])

    values = mod.load_env_file()

    assert values['OPENNEWS_TOKEN'] == 'real-token'
    assert values['TWITTER_TOKEN'] == 'real-token'
    assert values['OPEN_TOKEN'] == 'real-token'
