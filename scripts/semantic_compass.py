#!/usr/bin/env python3
"""Semantic Compass: agent-refreshable phrase pack for risk matching."""

from __future__ import annotations

import argparse
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_COMPASS_PATH = BASE_DIR / 'config' / 'semantic_compass.json'
DISPLAY_NAME = 'Semantic Compass'

DEFAULT_COMPASS = {
    'name': 'semantic_compass',
    'display_name': DISPLAY_NAME,
    'description': 'Agent-refreshed semantic phrase pack for geo-risk and news-risk matching.',
    'metadata': {
        'updated_at_utc': '',
        'source': 'repo_default',
        'last_refresh_brief': '',
        'last_refresh_status': 'idle',
    },
    'geo_risk': {
        'anchors': ['霍尔木兹海峡', '红海', '曼德海峡', '苏伊士运河', '伊朗', '以色列', '美军', '商船', '油轮', '航运'],
        'high': ['开战', '宣战', '空袭', '大规模袭击', '报复性打击', '直接参战', '原油运输中断', '商船遇袭'],
        'medium': ['航运改道', '停航', '战争风险保险', '油价飙升', '海上封锁', '港口关闭'],
        'shock': ['关闭霍尔木兹海峡', '海峡关闭', '暂停通行', '航运暂停', '海上封锁', '商船遇袭', '油轮遇袭', '原油运输中断'],
        'deescalation': ['尚未达到门槛', '不寻求升级', '保持克制', '通航自由', '保持开放', '航运未受干扰', '顺利通过', '恢复通航', '恢复通行'],
    },
    'news_risk': {
        'severe': ['exploit', 'hack', 'breach', 'attacker', 'blacklist', 'freeze', 'lawsuit', 'depeg', 'drains funds', '被盗', '黑客', '攻击', '漏洞', '冻结', '起诉'],
        'systemic': ['stablecoin', 'exchange outage', 'ETF rejection', 'regulatory crackdown', 'systemic risk', '交易所宕机', '监管打击', '流动性危机'],
        'benign_bullish': ['etf inflow', 'treasury accumulation', 'institutional demand', 'reserve strategy', 'buyback', '增持', '持续流入'],
        'isolated_project': ['ponzi', 'rug pull', '资金盘', '小市值项目', '冷门项目', 'meme token'],
    },
}

Runner = Callable[[str, Path], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def merge_unique_terms(*groups: list[str] | tuple[str, ...]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group or []:
            value = str(item or '').strip()
            if value and value not in merged:
                merged.append(value)
    return merged


def default_compass() -> dict[str, Any]:
    return deepcopy(DEFAULT_COMPASS)


def normalize_compass(payload: dict[str, Any] | None) -> dict[str, Any]:
    base = default_compass()
    current = payload or {}
    base['name'] = str(current.get('name') or base['name'])
    base['display_name'] = str(current.get('display_name') or base['display_name'])
    base['description'] = str(current.get('description') or base['description'])

    meta = current.get('metadata') or {}
    base['metadata'] = {
        **base['metadata'],
        'updated_at_utc': str(meta.get('updated_at_utc') or base['metadata']['updated_at_utc']),
        'source': str(meta.get('source') or base['metadata']['source']),
        'last_refresh_brief': str(meta.get('last_refresh_brief') or base['metadata']['last_refresh_brief']),
        'last_refresh_status': str(meta.get('last_refresh_status') or base['metadata']['last_refresh_status']),
    }

    for section in ('geo_risk', 'news_risk'):
        incoming = current.get(section) or {}
        for key, defaults in base[section].items():
            base[section][key] = merge_unique_terms(defaults, incoming.get(key) or [])
    return base


def load_semantic_compass(path: Path = DEFAULT_COMPASS_PATH, *, strict: bool = False) -> dict[str, Any]:
    if not path.exists():
        return default_compass()
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        if strict:
            raise ValueError(f'invalid semantic compass JSON at {path}') from exc
        return default_compass()
    if strict and not isinstance(payload, dict):
        raise ValueError(f'invalid semantic compass payload at {path}')
    return normalize_compass(payload)


def save_semantic_compass(payload: dict[str, Any], path: Path = DEFAULT_COMPASS_PATH) -> dict[str, Any]:
    normalized = normalize_compass(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return normalized


def summarize_counts(compass: dict[str, Any]) -> dict[str, int]:
    return {
        'geo_risk': sum(len(list((compass.get('geo_risk') or {}).get(key) or [])) for key in ('anchors', 'high', 'medium', 'shock', 'deescalation')),
        'news_risk': sum(len(list((compass.get('news_risk') or {}).get(key) or [])) for key in ('severe', 'systemic', 'benign_bullish', 'isolated_project')),
    }


def build_refresh_prompt(brief: str, compass_path: Path, current: dict[str, Any]) -> str:
    schema = {
        'name': 'semantic_compass',
        'display_name': DISPLAY_NAME,
        'description': 'Agent-refreshed semantic phrase pack for geo-risk and news-risk matching.',
        'metadata': {
            'updated_at_utc': 'ISO-8601 UTC timestamp',
            'source': 'agent_web_refresh',
            'last_refresh_brief': brief,
            'last_refresh_status': 'ok',
        },
        'geo_risk': {
            'anchors': ['地缘背景锚点短语'],
            'high': ['升级但未必是硬冲击'],
            'medium': ['风险升温但未确认冲击'],
            'shock': ['确认性冲击短语'],
            'deescalation': ['降温/恢复通航/未升级短语'],
        },
        'news_risk': {
            'severe': ['真正高风险新闻短语'],
            'systemic': ['系统性风险短语'],
            'benign_bullish': ['高影响但非风险的利多/中性短语'],
            'isolated_project': ['孤立项目事故/资金盘/非系统性短语'],
        },
    }
    return (
        '你在维护当前仓库中的风险语义词典。\n'
        '任务：使用联网搜索，严格审查后刷新 Semantic Compass。\n\n'
        f'刷新重点：{brief}\n'
        f'输出文件：{compass_path}\n\n'
        '要求：\n'
        '1. 必须联网搜索，优先采纳主流财经媒体、交易所公告、监管公告、国际媒体常见表述。\n'
        '2. 保留已有成熟短语，不要因为单次搜索把已经有效的老短语删光。\n'
        '3. 只保留真正适合规则匹配的短语；去重、去空、去过长句子。\n'
        '4. 对 geo_risk 明确区分 anchors / high / medium / shock / deescalation。\n'
        '5. 对 news_risk 明确区分 severe / systemic / benign_bullish / isolated_project。\n'
        '6. 直接把合法 JSON 写入目标文件，不要输出 YAML，不要写解释到文件里。\n'
        '7. metadata.updated_at_utc 写当前 UTC 时间；metadata.source 写 agent_web_refresh。\n\n'
        f'当前词典：\n```json\n{json.dumps(current, ensure_ascii=False, indent=2)}\n```\n\n'
        f'目标 JSON schema 示例：\n```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```\n'
    )


def build_hermes_refresh_command(prompt: str) -> list[str]:
    return [
        'hermes', 'chat', '-Q', '--source', 'tool', '--toolsets', 'web,file', '--max-turns', '40', '--query', prompt,
    ]


def run_hermes_refresh(prompt: str, path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        build_hermes_refresh_command(prompt),
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'semantic compass refresh failed')
    if not path.exists():
        raise RuntimeError(f'semantic compass file was not written: {path}')
    return {'ok': True, 'stdout': proc.stdout.strip()}


def refresh_semantic_compass(
    brief: str,
    path: Path = DEFAULT_COMPASS_PATH,
    runner: Runner = run_hermes_refresh,
) -> dict[str, Any]:
    normalized_brief = str(brief or '').strip() or '刷新 geo_risk 与 news_risk 语义短语，重点审查升级/降温/系统性风险表达。'
    current = load_semantic_compass(path)
    prompt = build_refresh_prompt(normalized_brief, path, current)
    runner_result = runner(prompt, path)
    refreshed = load_semantic_compass(path, strict=True)
    refreshed['metadata']['updated_at_utc'] = str(refreshed['metadata'].get('updated_at_utc') or utc_now())
    refreshed['metadata']['source'] = str(refreshed['metadata'].get('source') or 'agent_web_refresh')
    refreshed['metadata']['last_refresh_brief'] = normalized_brief
    refreshed['metadata']['last_refresh_status'] = 'ok'
    saved = save_semantic_compass(refreshed, path)
    return {
        'ok': True,
        'name': saved['name'],
        'display_name': saved['display_name'],
        'brief': normalized_brief,
        'updated_at': saved['metadata']['updated_at_utc'],
        'counts': summarize_counts(saved),
        'path': str(path),
        'runner': runner_result,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Refresh Semantic Compass using Hermes web research.')
    parser.add_argument('--brief', default='', help='Natural-language refresh brief for the phrase pack.')
    parser.add_argument('--path', default=str(DEFAULT_COMPASS_PATH), help='Output compass JSON path.')
    parser.add_argument('--print-prompt', action='store_true', help='Only print the generated Hermes prompt and exit.')
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    path = Path(args.path)
    if args.print_prompt:
        print(build_refresh_prompt(str(args.brief or '').strip(), path, load_semantic_compass(path)))
        return
    result = refresh_semantic_compass(brief=args.brief, path=path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
