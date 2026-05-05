#!/usr/bin/env python3
"""Canonical Phase3 pipeline runner.

Runs all Phase3 source fetchers, then the context builder, then the trigger
builder, and finally emits a unified markdown report plus a machine-readable
JSON summary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BASE_DIR = Path(__file__).resolve().parents[1]
WORKDIR = str(BASE_DIR)
REPORTS_DIR = BASE_DIR / 'reports'
CANONICAL_RUN_COMMAND = 'python scripts/phase3_pipeline.py'

SOURCE_STEPS = [
    {
        'id': 'okx_market',
        'role': 'social+hot_symbols',
        'script': 'scripts/sources/okx_market_fetch.py',
    },
    {
        'id': 'okx_positions',
        'role': 'holdings',
        'script': 'scripts/sources/okx_positions_fetch.py',
    },
    {
        'id': 'blockbeats',
        'role': 'macro+market_context+crypto_news',
        'script': 'scripts/sources/blockbeats_fetch.py',
    },
    {
        'id': 'cmc',
        'role': 'macro+market_context',
        'script': 'scripts/sources/cmc_fetch.py',
    },
    {
        'id': 'moss_xsignal',
        'role': 'macro+social_sentiment',
        'script': 'scripts/sources/moss_xsignal_fetch.py',
    },
    {
        'id': 'okx_news',
        'role': 'crypto_news',
        'script': 'scripts/sources/okx_news_fetch.py',
    },
    {
        'id': 'opennews',
        'role': 'crypto_news',
        'script': 'scripts/sources/opennews_fetch.py',
    },
    {
        'id': 'opentwitter',
        'role': 'social',
        'script': 'scripts/sources/opentwitter_fetch.py',
    },
    {
        'id': 'jin10',
        'role': 'macro',
        'script': 'scripts/sources/jin10_fetch.py',
    },
]

BUILDER_STEP = {
    'id': 'build_context_cache',
    'role': 'aggregation',
    'script': 'scripts/build_context_cache.py',
}

TRIGGER_STEP = {
    'id': 'build_triggers',
    'role': 'triggering',
    'script': 'scripts/build_triggers.py',
}


RunScriptFn = Callable[[str, str], dict[str, Any]]


def utc_now_slug() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def run_python_script(script_path: str, workdir: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ['python', script_path],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            'script': script_path,
            'exit_code': 124,
            'stdout': (exc.stdout or '').strip() if isinstance(exc.stdout, str) else '',
            'stderr': f'script timed out after {int(exc.timeout)} seconds',
        }
    return {
        'script': script_path,
        'exit_code': proc.returncode,
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }


def parse_step_stdout(stdout: str) -> dict[str, Any] | None:
    text = str(stdout or '').strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def step_succeeded(step_result: dict[str, Any]) -> bool:
    exit_code = step_result.get('exit_code', 1)
    if exit_code is None:
        exit_code = 1
    if int(exit_code) != 0:
        return False
    payload = parse_step_stdout(str(step_result.get('stdout') or ''))
    if isinstance(payload, dict) and payload.get('ok') is False:
        return False
    return True


def build_pipeline_summary(source_results: list[dict[str, Any]], builder_result: dict[str, Any], trigger_result: dict[str, Any]) -> dict[str, Any]:
    sources_ok = sum(1 for item in source_results if step_succeeded(item))
    sources_failed = len(source_results) - sources_ok
    builder_ok = step_succeeded(builder_result)
    trigger_ok = step_succeeded(trigger_result)
    return {
        'sources_ok': sources_ok,
        'sources_failed': sources_failed,
        'builder_ok': builder_ok,
        'trigger_ok': trigger_ok,
        'overall_ok': sources_failed == 0 and builder_ok and trigger_ok,
    }


def run_phase3(
    run_script: RunScriptFn = run_python_script,
    workdir: str = WORKDIR,
    parallel: bool = True,
) -> dict[str, Any]:
    def execute(step: dict[str, str]) -> dict[str, Any]:
        result = run_script(step['script'], workdir)
        parsed = parse_step_stdout(str(result.get('stdout') or ''))
        return {
            'id': step['id'],
            'role': step['role'],
            'ok': None if parsed is None else parsed.get('ok'),
            **result,
        }

    if parallel:
        with ThreadPoolExecutor(max_workers=len(SOURCE_STEPS)) as pool:
            unordered = list(pool.map(execute, SOURCE_STEPS))
        result_by_id = {item['id']: item for item in unordered}
        source_results = [result_by_id[step['id']] for step in SOURCE_STEPS]
    else:
        source_results = [execute(step) for step in SOURCE_STEPS]

    builder_result = {
        'id': BUILDER_STEP['id'],
        'role': BUILDER_STEP['role'],
        **run_script(BUILDER_STEP['script'], workdir),
    }
    trigger_result = {
        'id': TRIGGER_STEP['id'],
        'role': TRIGGER_STEP['role'],
        **run_script(TRIGGER_STEP['script'], workdir),
    }
    summary = build_pipeline_summary(source_results, builder_result, trigger_result)
    return {
        'ok': summary['overall_ok'],
        'workdir': workdir,
        'parallel': parallel,
        'sources': source_results,
        'builder': builder_result,
        'trigger': trigger_result,
        'summary': summary,
    }


def format_report(result: dict[str, Any]) -> str:
    lines = [
        '# Phase3 Unified Report',
        '',
        f"- Status: {'OK' if result.get('ok') else 'FAILED'}",
        f"- Workdir: `{result.get('workdir', WORKDIR)}`",
        f"- Mode: `{'parallel' if result.get('parallel', True) else 'sequential'}`",
        '',
        '## Canonical workflow',
        '',
        f'- Canonical command: `{CANONICAL_RUN_COMMAND}`',
        '- Standard sequence: run all source fetchers, then run the cache builder.',
        '',
        '## Summary',
        '',
        f"- Sources OK: {result.get('summary', {}).get('sources_ok', 0)}",
        f"- Sources failed: {result.get('summary', {}).get('sources_failed', 0)}",
        f"- Builder OK: {result.get('summary', {}).get('builder_ok', False)}",
        f"- Trigger OK: {result.get('summary', {}).get('trigger_ok', False)}",
        '',
        '## Source steps',
        '',
    ]
    for item in result.get('sources', []):
        lines.extend([
            f"### {item.get('id')}",
            f"- Role: `{item.get('role')}`",
            f"- Script: `{item.get('script')}`",
            f"- Exit code: `{item.get('exit_code')}`",
            '- Stdout:',
            '```json',
            item.get('stdout', ''),
            '```',
        ])
        if item.get('stderr'):
            lines.extend(['- Stderr:', '```', item.get('stderr', ''), '```'])
        lines.append('')

    builder = result.get('builder', {})
    lines.extend([
        '## Builder step',
        '',
        f"### {builder.get('id', 'build_context_cache')}",
        f"- Role: `{builder.get('role', 'aggregation')}`",
        f"- Script: `{builder.get('script', '')}`",
        f"- Exit code: `{builder.get('exit_code')}`",
        '- Stdout:',
        '```json',
        builder.get('stdout', ''),
        '```',
    ])
    if builder.get('stderr'):
        lines.extend(['- Stderr:', '```', builder.get('stderr', ''), '```'])
    lines.append('')

    trigger = result.get('trigger', {})
    lines.extend([
        '## Trigger step',
        '',
        f"### {trigger.get('id', 'build_triggers')}",
        f"- Role: `{trigger.get('role', 'triggering')}`",
        f"- Script: `{trigger.get('script', '')}`",
        f"- Exit code: `{trigger.get('exit_code')}`",
        '- Stdout:',
        '```json',
        trigger.get('stdout', ''),
        '```',
    ])
    if trigger.get('stderr'):
        lines.extend(['- Stderr:', '```', trigger.get('stderr', ''), '```'])
    lines.append('')

    return '\n'.join(lines)


def write_report(result: dict[str, Any], report_dir: Path = REPORTS_DIR) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f'phase3_report_{utc_now_slug()}.md'
    path.write_text(format_report(result), encoding='utf-8')
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the canonical Phase3 workflow and optionally write a unified report.')
    parser.add_argument('--sequential', action='store_true', help='Run source fetchers sequentially instead of in parallel.')
    parser.add_argument('--report-dir', default=str(REPORTS_DIR), help='Directory for the unified markdown report output.')
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])
    result = run_phase3(parallel=not args.sequential)
    report_path = write_report(result, report_dir=Path(args.report_dir))
    payload = {
        **result,
        'report_path': str(report_path),
        'canonical_command': CANONICAL_RUN_COMMAND,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not result.get('ok'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
