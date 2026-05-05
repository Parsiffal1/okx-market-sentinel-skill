from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/semantic_compass.py"


def load_module():
    spec = importlib.util.spec_from_file_location('semantic_compass_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_semantic_compass_returns_defaults_when_missing(tmp_path):
    mod = load_module()

    payload = mod.load_semantic_compass(tmp_path / 'missing.json')

    assert payload['name'] == 'semantic_compass'
    assert 'deescalation' in payload['geo_risk']
    assert payload['news_risk']['severe']


def test_build_hermes_refresh_command_uses_web_and_file_toolsets():
    mod = load_module()

    command = mod.build_hermes_refresh_command('PROMPT')

    assert command[:3] == ['hermes', 'chat', '-Q']
    assert 'web,file' in command
    assert 'PROMPT' in command


def test_refresh_semantic_compass_uses_runner_and_persists_updated_payload(tmp_path):
    mod = load_module()
    compass_path = tmp_path / 'semantic_compass.json'

    def fake_runner(prompt: str, path: Path) -> dict:
        assert '恢复通航' in prompt
        path.write_text(json.dumps({
            'name': 'semantic_compass',
            'geo_risk': {'deescalation': ['恢复通航'], 'shock': ['关闭霍尔木兹海峡']},
            'news_risk': {'severe': ['exploit'], 'benign_bullish': ['ETF inflow']},
        }, ensure_ascii=False), encoding='utf-8')
        return {'ok': True, 'stdout': 'done'}

    result = mod.refresh_semantic_compass(
        brief='补充恢复通航语义',
        path=compass_path,
        runner=fake_runner,
    )

    assert result['ok'] is True
    saved = json.loads(compass_path.read_text(encoding='utf-8'))
    assert saved['metadata']['last_refresh_brief'] == '补充恢复通航语义'
    assert '恢复通航' in saved['geo_risk']['deescalation']


def test_refresh_semantic_compass_rejects_invalid_written_json(tmp_path):
    mod = load_module()
    compass_path = tmp_path / 'semantic_compass.json'
    compass_path.write_text(json.dumps(mod.default_compass(), ensure_ascii=False), encoding='utf-8')

    def fake_runner(prompt: str, path: Path) -> dict:
        path.write_text('{invalid', encoding='utf-8')
        return {'ok': True, 'stdout': 'done'}

    try:
        mod.refresh_semantic_compass(brief='补充恢复通航语义', path=compass_path, runner=fake_runner)
        raised = None
    except ValueError as exc:
        raised = exc

    assert raised is not None
    assert 'invalid semantic compass' in str(raised).lower()
