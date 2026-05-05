from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "dashboard/server.py"
MODULE_DIR = MODULE_PATH.parent


def load_module():
    if str(MODULE_DIR) not in sys.path:
        sys.path.insert(0, str(MODULE_DIR))
    spec = importlib.util.spec_from_file_location('dashboard_server_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_artifacts(tmp_path: Path) -> tuple[Path, Path, Path]:
    context_path = tmp_path / 'context_cache.json'
    triggers_path = tmp_path / 'trigger_candidates.json'
    settings_path = tmp_path / 'dashboard_settings.json'
    context_path.write_text(json.dumps({'market_state': {'risk_state': 'medium'}, 'macro': {'regime_bias': 'neutral', 'risk_state': 'medium', 'event_window': False}, 'health': {'okx_market': 'ok'}, 'hot_symbols_state': {'top_tradeable_symbols': []}, 'crypto_news': {'high_impact_events': [], 'watchlist_events': [], 'security_events': []}, 'holdings_state': {'has_positions': False, 'symbol_risk': []}}, ensure_ascii=False), encoding='utf-8')
    triggers_path.write_text(json.dumps({'llm_wake_required': False, 'observe_only_triggers': [], 'hot_symbols_ranking': [], 'wake_state': {'llm_wake_required': False, 'observe_only_reasons': []}}, ensure_ascii=False), encoding='utf-8')
    settings_path.write_text(json.dumps({'backend_refresh_minutes': 30, 'frontend_poll_seconds': 10, 'theme': 'dark', 'compact_mode': False}, ensure_ascii=False), encoding='utf-8')
    return context_path, triggers_path, settings_path


def test_load_dashboard_settings_returns_defaults_when_missing(tmp_path):
    mod = load_module()
    payload = mod.load_dashboard_settings(tmp_path / 'missing.json')
    assert payload == {
        'backend_refresh_minutes': 30,
        'frontend_poll_seconds': 10,
        'theme': 'dark',
        'compact_mode': False,
        'semantic_compass_focus': '',
        'semantic_compass_last_brief': '',
        'semantic_compass_last_updated_at': '',
        'semantic_compass_refresh_status': 'idle',
    }


def test_dashboard_service_returns_aggregated_dashboard_payload(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)
    service = mod.DashboardService(context_path=context_path, triggers_path=triggers_path, settings_path=settings_path)

    payload = service.get_dashboard_payload()

    assert payload['settings']['backend_refresh_minutes'] == 30
    assert payload['summary']['regime_bias'] == 'neutral'
    assert payload['summary']['risk_state'] == 'medium'


def test_dashboard_service_updates_settings_and_persists_to_disk(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)
    service = mod.DashboardService(context_path=context_path, triggers_path=triggers_path, settings_path=settings_path)

    payload = service.update_settings({'backend_refresh_minutes': 15, 'frontend_poll_seconds': 5, 'theme': 'dark', 'compact_mode': True})

    assert payload['backend_refresh_minutes'] == 15
    assert payload['frontend_poll_seconds'] == 5
    assert payload['compact_mode'] is True
    saved = json.loads(settings_path.read_text(encoding='utf-8'))
    assert saved['backend_refresh_minutes'] == 15


def test_dashboard_service_ignores_runtime_status_fields_in_user_settings_updates(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)
    service = mod.DashboardService(context_path=context_path, triggers_path=triggers_path, settings_path=settings_path)

    payload = service.update_settings({
        'backend_refresh_minutes': 20,
        'semantic_compass_refresh_status': 'ok',
        'semantic_compass_last_updated_at': '2026-01-01T00:00:00Z',
    })

    assert payload['backend_refresh_minutes'] == 20
    assert payload['semantic_compass_refresh_status'] == 'idle'
    assert payload['semantic_compass_last_updated_at'] == ''


def test_dashboard_service_rejects_non_object_settings_payload(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)
    service = mod.DashboardService(context_path=context_path, triggers_path=triggers_path, settings_path=settings_path)

    try:
        service.update_settings(['bad'])
    except ValueError as exc:
        assert 'object' in str(exc)
    else:
        raise AssertionError('expected ValueError for non-object settings payload')


def test_dashboard_service_rejects_non_numeric_poll_seconds(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)
    service = mod.DashboardService(context_path=context_path, triggers_path=triggers_path, settings_path=settings_path)

    try:
        service.update_settings({'frontend_poll_seconds': 'abc'})
    except ValueError as exc:
        assert 'frontend_poll_seconds' in str(exc)
    else:
        raise AssertionError('expected ValueError for invalid frontend_poll_seconds')


def test_dashboard_service_manual_refresh_uses_runner(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)
    calls = []

    def fake_runner() -> dict:
        calls.append('run')
        return {'ok': True, 'report_path': '/tmp/report.md'}

    service = mod.DashboardService(context_path=context_path, triggers_path=triggers_path, settings_path=settings_path, refresh_runner=fake_runner)
    result = service.run_refresh()

    assert calls == ['run']
    assert result['ok'] is True
    assert result['report_path'] == '/tmp/report.md'


def test_dashboard_service_refreshes_semantic_compass_and_persists_metadata(tmp_path):
    mod = load_module()
    context_path, triggers_path, settings_path = write_artifacts(tmp_path)

    def fake_compass_runner(brief: str) -> dict:
        assert '霍尔木兹' in brief
        return {
            'ok': True,
            'name': 'semantic_compass',
            'brief': brief,
            'updated_at': '2026-05-05T14:00:00Z',
            'counts': {'geo_risk': 12, 'news_risk': 8},
        }

    service = mod.DashboardService(
        context_path=context_path,
        triggers_path=triggers_path,
        settings_path=settings_path,
        compass_refresh_runner=fake_compass_runner,
    )
    result = service.run_semantic_compass_refresh('补充霍尔木兹关闭与恢复通航语义')

    assert result['ok'] is True
    saved = json.loads(settings_path.read_text(encoding='utf-8'))
    assert saved['semantic_compass_last_brief'] == '补充霍尔木兹关闭与恢复通航语义'
    assert saved['semantic_compass_last_updated_at'] == '2026-05-05T14:00:00Z'
    assert saved['semantic_compass_refresh_status'] == 'ok'



def test_parse_args_supports_public_host_binding():
    mod = load_module()

    args = mod.parse_args(['--host', '0.0.0.0', '--port', '8877'])

    assert args.host == '0.0.0.0'
    assert args.port == 8877


def test_build_access_urls_returns_local_and_public_candidates():
    mod = load_module()

    payload = mod.build_access_urls(host='0.0.0.0', port=8765, server_ip='203.0.113.10')

    assert payload['bind'] == '0.0.0.0:8765'
    assert payload['local_url'] == 'http://127.0.0.1:8765'
    assert payload['public_url'] == 'http://203.0.113.10:8765'


def test_build_access_urls_does_not_report_zero_host_as_public_url_when_no_candidate_exists():
    mod = load_module()

    payload = mod.build_access_urls(host='0.0.0.0', port=8765, server_ip=None)

    assert payload['bind'] == '0.0.0.0:8765'
    assert payload['public_url'] is None
