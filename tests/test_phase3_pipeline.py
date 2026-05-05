from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/phase3_pipeline.py"


def load_module():
    spec = importlib.util.spec_from_file_location('phase3_pipeline_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_phase3_pipeline_declares_all_sources_and_builder():
    mod = load_module()

    source_ids = [step['id'] for step in mod.SOURCE_STEPS]
    assert source_ids == ['okx_market', 'okx_positions', 'blockbeats', 'cmc', 'moss_xsignal', 'okx_news', 'opennews', 'opentwitter', 'jin10']
    assert mod.BUILDER_STEP['id'] == 'build_context_cache'
    assert mod.TRIGGER_STEP['id'] == 'build_triggers'
    assert mod.SOURCE_STEPS[7]['role'] == 'social'
    assert mod.CANONICAL_RUN_COMMAND == 'python scripts/phase3_pipeline.py'


def test_run_phase3_executes_sources_then_builder_with_summary():
    mod = load_module()
    calls = []

    def fake_run_script(script_path: str, workdir: str):
        calls.append(Path(script_path).name)
        return {
            'script': script_path,
            'exit_code': 0,
            'stdout': f'ran {Path(script_path).name}',
            'stderr': '',
        }

    result = mod.run_phase3(run_script=fake_run_script, workdir='/tmp/crypto-agent', parallel=False)

    assert calls == [
        'okx_market_fetch.py',
        'okx_positions_fetch.py',
        'blockbeats_fetch.py',
        'cmc_fetch.py',
        'moss_xsignal_fetch.py',
        'okx_news_fetch.py',
        'opennews_fetch.py',
        'opentwitter_fetch.py',
        'jin10_fetch.py',
        'build_context_cache.py',
        'build_triggers.py',
    ]
    assert result['ok'] is True
    assert result['builder']['script'].endswith('build_context_cache.py')
    assert result['trigger']['script'].endswith('build_triggers.py')
    assert [item['id'] for item in result['sources']] == ['okx_market', 'okx_positions', 'blockbeats', 'cmc', 'moss_xsignal', 'okx_news', 'opennews', 'opentwitter', 'jin10']


def test_run_phase3_treats_stdout_ok_false_as_failure_even_when_exit_code_is_zero():
    mod = load_module()

    def fake_run_script(script_path: str, workdir: str):
        name = Path(script_path).name
        if name == 'opennews_fetch.py':
            return {
                'script': script_path,
                'exit_code': 0,
                'stdout': json.dumps({'ok': False, 'source': 'opennews', 'message': 'paid quota exhausted'}),
                'stderr': '',
            }
        return {
            'script': script_path,
            'exit_code': 0,
            'stdout': json.dumps({'ok': True}),
            'stderr': '',
        }

    result = mod.run_phase3(run_script=fake_run_script, workdir='/tmp/crypto-agent', parallel=False)

    failing_source = next(item for item in result['sources'] if item['id'] == 'opennews')
    assert failing_source['ok'] is False
    assert result['summary']['sources_failed'] == 1
    assert result['ok'] is False


def test_build_pipeline_summary_counts_failures():
    mod = load_module()
    summary = mod.build_pipeline_summary(
        source_results=[
            {'id': 'blockbeats', 'exit_code': 0},
            {'id': 'okx_news', 'exit_code': 1},
        ],
        builder_result={'id': 'build_context_cache', 'exit_code': 0},
        trigger_result={'id': 'build_triggers', 'exit_code': 0},
    )

    assert summary == {
        'sources_ok': 1,
        'sources_failed': 1,
        'builder_ok': True,
        'trigger_ok': True,
        'overall_ok': False,
    }


def test_run_python_script_returns_structured_timeout_result(monkeypatch):
    mod = load_module()

    def fake_run(*args, **kwargs):
        raise mod.subprocess.TimeoutExpired(cmd=['python', 'slow.py'], timeout=300)

    monkeypatch.setattr(mod.subprocess, 'run', fake_run)

    result = mod.run_python_script('scripts/sources/slow.py', '/tmp/crypto-agent')

    assert result['script'] == 'scripts/sources/slow.py'
    assert result['exit_code'] == 124
    assert 'timed out' in result['stderr'].lower()


def test_format_report_contains_workflow_standard_and_step_details():
    mod = load_module()
    report = mod.format_report(
        {
            'workdir': '/tmp/crypto-agent',
            'sources': [
                {
                    'id': 'opentwitter',
                    'role': 'social',
                    'script': 'scripts/sources/opentwitter_fetch.py',
                    'exit_code': 0,
                    'stdout': '{"ok": true}',
                    'stderr': '',
                }
            ],
            'builder': {
                'id': 'build_context_cache',
                'role': 'aggregation',
                'script': 'scripts/build_context_cache.py',
                'exit_code': 0,
                'stdout': '{"ok": true}',
                'stderr': '',
            },
            'trigger': {
                'id': 'build_triggers',
                'role': 'triggering',
                'script': 'scripts/build_triggers.py',
                'exit_code': 0,
                'stdout': '{"ok": true}',
                'stderr': '',
            },
            'summary': {
                'sources_ok': 1,
                'sources_failed': 0,
                'builder_ok': True,
                'trigger_ok': True,
                'overall_ok': True,
            },
            'ok': True,
        }
    )

    assert '# Phase3 Unified Report' in report
    assert 'Canonical workflow' in report
    assert 'python scripts/phase3_pipeline.py' in report
    assert 'opentwitter' in report
    assert 'build_context_cache' in report
    assert 'build_triggers' in report


def test_write_report_creates_markdown_file(tmp_path):
    mod = load_module()
    payload = {
        'workdir': '/tmp/crypto-agent',
        'sources': [],
        'builder': {'id': 'build_context_cache', 'role': 'aggregation', 'script': 'scripts/build_context_cache.py', 'exit_code': 0, 'stdout': '{}', 'stderr': ''},
        'trigger': {'id': 'build_triggers', 'role': 'triggering', 'script': 'scripts/build_triggers.py', 'exit_code': 0, 'stdout': '{}', 'stderr': ''},
        'summary': {'sources_ok': 0, 'sources_failed': 0, 'builder_ok': True, 'trigger_ok': True, 'overall_ok': True},
        'ok': True,
    }

    report_path = mod.write_report(payload, report_dir=tmp_path)
    content = report_path.read_text(encoding='utf-8')

    assert report_path.name.startswith('phase3_report_')
    assert report_path.suffix == '.md'
    assert '# Phase3 Unified Report' in content
    assert 'Canonical workflow' in content


def test_main_writes_json_and_report_when_requested(tmp_path, monkeypatch, capsys):
    mod = load_module()

    def fake_run_phase3(**kwargs):
        return {
            'ok': True,
            'workdir': '/tmp/crypto-agent',
            'sources': [],
            'builder': {'id': 'build_context_cache', 'role': 'aggregation', 'script': 'scripts/build_context_cache.py', 'exit_code': 0, 'stdout': json.dumps({'ok': True}), 'stderr': ''},
            'trigger': {'id': 'build_triggers', 'role': 'triggering', 'script': 'scripts/build_triggers.py', 'exit_code': 0, 'stdout': json.dumps({'ok': True}), 'stderr': ''},
            'summary': {'sources_ok': 0, 'sources_failed': 0, 'builder_ok': True, 'trigger_ok': True, 'overall_ok': True},
        }

    monkeypatch.setattr(mod, 'run_phase3', fake_run_phase3)
    monkeypatch.setattr(mod.sys, 'argv', ['phase3_pipeline.py', '--sequential', '--report-dir', str(tmp_path)])

    mod.main()
    output = json.loads(capsys.readouterr().out)

    assert output['ok'] is True
    assert output['report_path'].endswith('.md')
    assert Path(output['report_path']).exists()


def test_main_exits_nonzero_when_pipeline_result_is_not_ok(tmp_path, monkeypatch, capsys):
    mod = load_module()

    def fake_run_phase3(**kwargs):
        return {
            'ok': False,
            'workdir': '/tmp/crypto-agent',
            'sources': [],
            'builder': {'id': 'build_context_cache', 'role': 'aggregation', 'script': 'scripts/build_context_cache.py', 'exit_code': 0, 'stdout': json.dumps({'ok': True}), 'stderr': ''},
            'trigger': {'id': 'build_triggers', 'role': 'triggering', 'script': 'scripts/build_triggers.py', 'exit_code': 0, 'stdout': json.dumps({'ok': True}), 'stderr': ''},
            'summary': {'sources_ok': 0, 'sources_failed': 1, 'builder_ok': True, 'trigger_ok': True, 'overall_ok': False},
        }

    monkeypatch.setattr(mod, 'run_phase3', fake_run_phase3)
    monkeypatch.setattr(mod.sys, 'argv', ['phase3_pipeline.py', '--report-dir', str(tmp_path)])

    try:
        mod.main()
        raised = None
    except SystemExit as exc:
        raised = exc

    output = json.loads(capsys.readouterr().out)
    assert output['ok'] is False
    assert raised is not None
    assert raised.code == 1
