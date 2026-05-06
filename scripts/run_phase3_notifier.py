#!/usr/bin/env python3
"""Run Phase3 and push a Telegram summary/report without using an LLM."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import requests
import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
CONTEXT_DIR = BASE_DIR / 'context'
REPORTS_DIR = BASE_DIR / 'reports'
HERMES_ENV_FILE = Path('/root/.hermes/.env')
HERMES_CONFIG_FILE = Path('/root/.hermes/config.yaml')
PHASE3_COMMAND = ['python', 'scripts/phase3_pipeline.py', '--sequential']
CONTEXT_CACHE_FILE = CONTEXT_DIR / 'context_cache.json'
TRIGGER_FILE = CONTEXT_DIR / 'trigger_candidates.json'
NOTIFIER_SNAPSHOT_FILE = CONTEXT_DIR / 'last_notifier_snapshot.json'


def utc_now_slug() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def load_simple_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_telegram_credentials() -> tuple[str, str]:
    env = load_simple_env(HERMES_ENV_FILE)
    token = env.get('PHASE3_NOTIFY_TELEGRAM_BOT_TOKEN') or env.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = env.get('PHASE3_NOTIFY_TELEGRAM_CHAT_ID', '')
    if HERMES_CONFIG_FILE.exists():
        payload = yaml.safe_load(HERMES_CONFIG_FILE.read_text(encoding='utf-8')) or {}
        if not chat_id:
            chat_id = str(payload.get('TELEGRAM_HOME_CHANNEL', '') or '')
    return token, chat_id


def run_phase3_pipeline() -> dict[str, Any]:
    proc = subprocess.run(PHASE3_COMMAND, cwd=BASE_DIR, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'phase3 pipeline failed')
    payload = json.loads(proc.stdout)
    if payload.get('ok') is False:
        raise RuntimeError(payload.get('summary', {}).get('message') or proc.stdout.strip() or 'phase3 pipeline reported failure')
    return payload


def load_context_payload(path: Path = CONTEXT_CACHE_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def load_trigger_payload(path: Path = TRIGGER_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def trigger_hot_ranking_items(triggers: dict[str, Any]) -> list[dict[str, Any]]:
    items = triggers.get('hot_symbols_ranking')
    if isinstance(items, list):
        return items
    return []


def build_notification_snapshot(context: dict[str, Any], triggers: dict[str, Any]) -> dict[str, Any]:
    macro = context.get('macro', {}) or {}
    crypto_news = context.get('crypto_news', {}) or {}
    return {
        'holdings': [str(symbol).strip().upper() for symbol in context.get('holdings', {}).get('prioritized_symbols', []) if str(symbol).strip()],
        'macro': {
            'regime': str(macro.get('regime', 'unknown')),
            'regime_bias': str(macro.get('regime_bias', macro.get('regime', 'unknown'))),
            'risk_state': str(macro.get('risk_state', 'unknown')),
            'geo_risk': str(macro.get('geo_risk', 'unknown')),
            'event_window': bool(macro.get('event_window')),
        },
        'llm_wake_required': bool(triggers.get('llm_wake_required')),
        'observe_only_triggers': [
            str(item.get('trigger_type', '')).strip()
            for item in triggers.get('observe_only_triggers', [])
            if str(item.get('trigger_type', '')).strip()
        ],
        'hot_symbols_ranking': [
            str(item.get('symbol', '')).strip().upper()
            for item in trigger_hot_ranking_items(triggers)
            if str(item.get('symbol', '')).strip()
        ],
        'news_titles': [
            str(item.get('title', '')).strip()
            for item in crypto_news.get('high_impact_events', [])[:3]
            if str(item.get('title', '')).strip()
        ],
    }


def load_notification_snapshot(path: Path = NOTIFIER_SNAPSHOT_FILE) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def write_notification_snapshot(snapshot: dict[str, Any], path: Path = NOTIFIER_SNAPSHOT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_change_summary(
    previous_context: dict[str, Any],
    previous_triggers: dict[str, Any],
    current_context: dict[str, Any],
    current_triggers: dict[str, Any],
) -> dict[str, Any]:
    previous = build_notification_snapshot(previous_context, previous_triggers) if previous_context or previous_triggers else {}
    current = build_notification_snapshot(current_context, current_triggers)
    if not previous:
        return {
            'has_changes': True,
            'lines': ['## 状态变化', '- 首次运行：已生成完整 Phase3 快照'],
        }

    lines: list[str] = []

    if previous.get('holdings') != current.get('holdings'):
        prev_holdings = ', '.join(previous.get('holdings', [])) or '无'
        curr_holdings = ', '.join(current.get('holdings', [])) or '无'
        lines.append(f'- 持仓：`{prev_holdings}` → `{curr_holdings}`')

    previous_macro = previous.get('macro', {}) or {}
    current_macro = current.get('macro', {}) or {}
    if previous_macro.get('regime_bias') != current_macro.get('regime_bias'):
        lines.append(f"- 方向偏置：`{previous_macro.get('regime_bias', 'unknown')}` → `{current_macro.get('regime_bias', 'unknown')}`")
    if previous_macro.get('risk_state') != current_macro.get('risk_state'):
        lines.append(f"- 风险等级：`{previous_macro.get('risk_state', 'unknown')}` → `{current_macro.get('risk_state', 'unknown')}`")
    if previous_macro.get('geo_risk') != current_macro.get('geo_risk'):
        lines.append(f"- 地缘风险：`{previous_macro.get('geo_risk', 'unknown')}` → `{current_macro.get('geo_risk', 'unknown')}`")
    if previous_macro.get('event_window') != current_macro.get('event_window'):
        prev_window = '是' if previous_macro.get('event_window') else '否'
        curr_window = '是' if current_macro.get('event_window') else '否'
        lines.append(f'- 事件窗口：`{prev_window}` → `{curr_window}`')

    if previous.get('llm_wake_required') != current.get('llm_wake_required'):
        prev_wake = '是' if previous.get('llm_wake_required') else '否'
        curr_wake = '是' if current.get('llm_wake_required') else '否'
        lines.append(f'- LLM 唤醒：`{prev_wake}` → `{curr_wake}`')

    if previous.get('observe_only_triggers') != current.get('observe_only_triggers'):
        prev_observe = ', '.join(previous.get('observe_only_triggers', [])) or '无'
        curr_observe = ', '.join(current.get('observe_only_triggers', [])) or '无'
        lines.append(f'- 观察级触发：`{prev_observe}` → `{curr_observe}`')

    if previous.get('hot_symbols_ranking') != current.get('hot_symbols_ranking'):
        prev_hot = ', '.join(previous.get('hot_symbols_ranking', [])) or '无'
        curr_hot = ', '.join(current.get('hot_symbols_ranking', [])) or '无'
        lines.append(f'- 热度排名：`{prev_hot}` → `{curr_hot}`')

    previous_news = previous.get('news_titles', []) or []
    current_news = current.get('news_titles', []) or []
    added_news = [title for title in current_news if title not in previous_news]
    removed_news = [title for title in previous_news if title not in current_news]
    if added_news:
        lines.append('- 新增重点新闻：' + ' | '.join(added_news[:3]))
    if removed_news:
        lines.append('- 移除重点新闻：' + ' | '.join(removed_news[:3]))

    if not lines:
        lines = ['哨兵：本轮无重要变化，无新增重要新闻，继续观察市场。']
    else:
        lines = ['## 状态变化', *lines]

    return {
        'has_changes': lines[0] != '哨兵：本轮无重要变化，无新增重要新闻，继续观察市场。',
        'lines': lines,
    }


def build_semantic_macro_lines(context: dict[str, Any]) -> dict[str, list[str]]:
    macro = context.get('macro', {}) or {}
    buckets = macro.get('summary_buckets', {}) or {}
    geo_lines = [str(item).strip() for item in (buckets.get('geo', []) or []) if str(item).strip()]
    macro_financial_lines = [str(item).strip() for item in (buckets.get('macro_financial', []) or []) if str(item).strip()]
    us_equity_lines = [str(item).strip() for item in (buckets.get('us_equity_sentiment', []) or []) if str(item).strip()]
    if not geo_lines and not macro_financial_lines:
        geo_lines = [str(item).strip() for item in (macro.get('macro_summary', []) or [])[:3] if str(item).strip()]
    return {
        'macro_geo': geo_lines + macro_financial_lines,
        'us_equity': us_equity_lines,
    }



def html_escape(value: Any) -> str:
    text = str(value if value is not None else '')
    return (
        text.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def html_bold(text: str) -> str:
    return f'<b>{html_escape(text)}</b>'


def html_code(text: str) -> str:
    return f'<code>{html_escape(text)}</code>'


def html_pre(lines: list[str]) -> str:
    return '<pre>' + html_escape('\n'.join(lines)) + '</pre>'


def humanize_hot_symbol_source(source: str) -> str:
    mapping = {
        'holding': '持仓优先',
        'social': '社媒热议',
        'social_hot_list': '社媒热议',
        'cmc': 'CMC趋势',
        'cmc_trending_okx_listed': 'CMC趋势',
        'okx_top_gainers': 'OKX涨幅榜',
        'okx_oi_change': 'OKX持仓异动',
        'okx_oi': 'OKX高持仓',
        'okx_top_oi': 'OKX高持仓',
    }
    return mapping.get(str(source or '').strip(), str(source or '').strip() or '未知来源')


def humanize_hot_symbol_reason(reason: str) -> str:
    mapping = {
        'existing_holding': '持仓标的',
        'high_social_heat': '社媒高热',
        'multi_account_discussion': '多账户共识',
        'social_symbol_mention': '社媒提及',
        'cmc_trending_symbol': 'CMC趋势上榜',
        'okx_oi_price_up_quadrant': 'OI↑ 价格↑（偏新多）',
        'okx_oi_short_build_quadrant': 'OI↑ 价格↓（偏新空）',
        'okx_oi_short_cover_quadrant': 'OI↓ 价格↑（偏空头回补）',
        'okx_oi_long_exit_quadrant': 'OI↓ 价格↓（偏多头离场）',
        'okx_oi_change_leader': 'OI异动靠前',
        'okx_top_gainer_24h': '24h涨幅靠前',
        'okx_top_oi_contract': '持仓量靠前',
    }
    return mapping.get(str(reason or '').strip(), str(reason or '').strip() or '其他')


def render_hot_symbol_sources(sources: list[str]) -> str:
    labels: list[str] = []
    for source in sources:
        label = humanize_hot_symbol_source(source)
        if label and label not in labels:
            labels.append(label)
    return ' + '.join(labels) or '未知来源'


def render_hot_symbol_reasons(reasons: list[str]) -> str:
    labels: list[str] = []
    for reason in reasons:
        label = humanize_hot_symbol_reason(reason)
        if label and label not in labels:
            labels.append(label)
    return '；'.join(labels) or '无明确原因'


def render_news_title_with_source(event: dict[str, Any]) -> str:
    title = str(event.get('title') or '').strip()
    source = str(event.get('source') or 'unknown').strip()
    if not title:
        return ''
    return f'{title}（来源: {source}）'


def build_trigger_status_block(context: dict[str, Any], triggers: dict[str, Any]) -> str:
    macro = context.get('macro', {}) or {}
    crypto_news = context.get('crypto_news', {}) or {}

    macro_confluence = (
        (macro.get('regime_bias') or macro.get('regime')) == 'bearish'
        and macro.get('geo_risk') == 'high'
        and bool(macro.get('event_window'))
        and crypto_news.get('news_risk') == 'high'
    )
    security_states = [str(item.get('state') or '').strip().lower() for item in crypto_news.get('security_events', [])]
    has_live_security = any(state == 'live_exploit' for state in security_states)
    has_followup_security = any(state in {'post_exploit_active', 'postmortem'} for state in security_states)
    held_security_state = 'live_exploit' if has_live_security else ('后续跟进（不唤醒）' if has_followup_security else '无')
    held_event_cluster = any(item.get('trigger_type') == 'held_symbol_event_cluster' for item in triggers.get('llm_wake_triggers', []))
    observe_types = ', '.join(item.get('trigger_type', '') for item in triggers.get('observe_only_triggers', []) if item.get('trigger_type')) or '无'
    wake_state = '是' if triggers.get('llm_wake_required') else '否'

    return html_pre([
        f"宏观四因子共振 : {'已触发' if macro_confluence else '未触发'}",
        f'持仓安全事件   : {held_security_state}',
        f"持仓事件簇     : {'已触发' if held_event_cluster else '无'}",
        f'LLM 唤醒       : {wake_state}',
        f'观察级触发     : {observe_types}',
    ])


def build_hot_symbols_ranking_lines(triggers: dict[str, Any]) -> list[str]:
    items = trigger_hot_ranking_items(triggers)
    grouped = {
        'holding': [],
        'social_hot_list': [],
        'cmc_trending_okx_listed': [],
        'okx_top_gainers': [],
        'okx_oi_change': [],
        'okx_oi': [],
    }
    for item in items:
        source = str(item.get('source') or '').strip()
        symbol = str(item.get('symbol') or '').strip().upper()
        if not symbol or not source:
            continue
        for source_part in source.split('+'):
            normalized = {
                'cmc': 'cmc_trending_okx_listed',
                'social': 'social_hot_list',
                'okx_top_oi': 'okx_oi',
                'okx_top_gainers': 'okx_top_gainers',
                'okx_oi_change': 'okx_oi_change',
                'holding': 'holding',
            }.get(source_part.strip(), source_part.strip())
            if normalized in grouped and symbol not in grouped[normalized]:
                grouped[normalized].append(symbol)

    current_list = ', '.join(str(item.get('symbol') or '').strip().upper() for item in items if str(item.get('symbol') or '').strip()) or '无'
    return [
        f'• 当前列表: {html_code(current_list)}',
        f"• 持仓优先: {html_code(', '.join(grouped['holding']) or '无')}",
        f"• 白名单热议: {html_code(', '.join(grouped['social_hot_list']) or '无')}",
        f"• CMC 补充: {html_code(', '.join(grouped['cmc_trending_okx_listed']) or '无')}",
        f"• OKX涨幅榜: {html_code(', '.join(grouped['okx_top_gainers']) or '无')}",
        f"• OKX持仓异动: {html_code(', '.join(grouped['okx_oi_change']) or '无')}",
        f"• OKX高持仓: {html_code(', '.join(grouped['okx_oi']) or '无')}",
    ]


def build_holdings_risk_lines(context: dict[str, Any], limit: int = 3) -> list[str]:
    holdings_state = context.get('holdings_state', {}) or {}
    rows = holdings_state.get('symbol_risk', []) or []
    lines: list[str] = []
    for index, item in enumerate(rows[:limit], start=1):
        symbol = str(item.get('symbol') or '').strip().upper()
        if not symbol:
            continue
        risk_state = str(item.get('risk_state') or 'unknown').strip()
        event_count = int(item.get('relevant_event_count', 0) or 0)
        social_heat = int(item.get('relevant_social_heat', 0) or 0)
        reasons = ', '.join(str(reason).strip() for reason in (item.get('reasons') or []) if str(reason).strip())
        line = f'{index}. {html_escape(symbol)} ｜ risk={html_escape(risk_state)} ｜ events={event_count} ｜ heat={social_heat}'
        if reasons:
            line += f' ｜ reasons={html_escape(reasons)}'
        lines.append(line)
    return lines


def build_hot_symbols_lines(context: dict[str, Any], limit: int = 3) -> list[str]:
    hot_symbols_state = context.get('hot_symbols_state', {}) or {}
    rows = hot_symbols_state.get('top_tradeable_symbols', []) or []
    lines: list[str] = []
    for index, item in enumerate(rows[:limit], start=1):
        symbol = str(item.get('symbol') or '').strip().upper()
        if not symbol:
            continue
        score = int(item.get('score', 0) or 0)
        sources = render_hot_symbol_sources([str(source).strip() for source in (item.get('sources') or []) if str(source).strip()])
        reasons = render_hot_symbol_reasons([str(reason).strip() for reason in (item.get('reasons') or []) if str(reason).strip()])
        lines.append(
            f'{index}. {html_escape(symbol)} ｜ 评分={score} ｜ 来源={html_escape(sources)} ｜ 原因={html_escape(reasons)}'
        )
    return lines


def build_health_block(context: dict[str, Any]) -> str:
    health = context.get('health', {}) or {}
    if not health:
        return '• 无 health 数据'
    core_sources = ['blockbeats', 'cmc', 'moss_xsignal', 'jin10', 'okx_news', 'okx_market']
    aux_sources = ['okx_positions', 'opennews', 'opentwitter']

    def render_group(names: list[str]) -> str:
        return ' | '.join(f'{name}:{health[name]}' for name in names if name in health) or '无'

    return html_pre([
        f'核心  {render_group(core_sources)}',
        f'辅助  {render_group(aux_sources)}',
    ])


def build_notification_message(
    pipeline_result: dict[str, Any],
    context: dict[str, Any],
    triggers: dict[str, Any],
    change_summary: dict[str, Any] | None = None,
    report_path: str | None = None,
) -> str:
    holdings = ', '.join(context.get('holdings', {}).get('prioritized_symbols', [])) or '无'
    macro = context.get('macro', {}) or {}
    crypto_news = context.get('crypto_news', {}) or {}
    semantic_macro = build_semantic_macro_lines(context)
    macro_geo_lines = semantic_macro['macro_geo'][:2]
    us_equity_lines = semantic_macro['us_equity'][:1]
    security_events = [item for item in crypto_news.get('security_events', [])[:1] if str(item.get('title') or '').strip()]
    high_impact_events = [item for item in crypto_news.get('high_impact_events', [])[:2] if str(item.get('title') or '').strip()]
    new_event_rows = [item for item in crypto_news.get('new_high_impact_events', [])[:1] if str(item.get('title') or '').strip()]
    watch_event_rows = [item for item in crypto_news.get('watchlist_events', [])[:2] if str(item.get('title') or '').strip()]
    security_title_keys = {str(item.get('title') or '').strip() for item in security_events}
    new_event_rows = [item for item in new_event_rows if str(item.get('title') or '').strip() not in security_title_keys]
    new_title_keys = {str(item.get('title') or '').strip() for item in new_event_rows}
    watch_event_rows = [item for item in watch_event_rows if str(item.get('title') or '').strip() not in security_title_keys and str(item.get('title') or '').strip() not in new_title_keys]
    security_titles = [render_news_title_with_source(item) for item in security_events]
    news_titles = [render_news_title_with_source(item) for item in high_impact_events]
    new_titles = [render_news_title_with_source(item) for item in new_event_rows]
    watch_titles = [render_news_title_with_source(item) for item in watch_event_rows]
    observe_types = ', '.join(item.get('trigger_type', '') for item in triggers.get('observe_only_triggers', []) if item.get('trigger_type')) or '无'
    status_ok = bool(pipeline_result.get('ok', pipeline_result.get('summary', {}).get('overall_ok')))
    regime_bias = str(macro.get('regime_bias') or macro.get('regime') or 'unknown')
    risk_state = str(macro.get('risk_state') or 'unknown')
    hot_ranking_summary = ', '.join(item.get('symbol', '') for item in trigger_hot_ranking_items(triggers) if item.get('symbol')) or '无'

    if change_summary and not change_summary.get('has_changes'):
        return '\n'.join([
            html_bold('OKX 市场哨兵｜本轮无重要变化'),
            f'持仓: {html_code(holdings)}',
            f'方向/风险: {html_code(regime_bias + " / " + risk_state)}',
            f'观察级触发: {html_code(observe_types)}',
            f'热度排名: {html_code(hot_ranking_summary)}',
        ])

    lines = [
        html_bold('OKX 市场哨兵｜运行完成'),
        f"• 状态: {html_code('正常' if status_ok else '异常')}",
        f'• 持仓: {html_code(holdings)}',
        f'• 方向偏置: {html_code(regime_bias)}',
        f'• 风险等级: {html_code(risk_state)}',
        f"• LLM 唤醒: {html_code('是' if triggers.get('llm_wake_required') else '否')}",
        f'• 观察级触发: {html_code(observe_types)}',
    ]
    lines.extend([
        '',
        html_bold('Trigger 判定'),
        build_trigger_status_block(context, triggers),
        '',
        html_bold('热度排名'),
        *build_hot_symbols_ranking_lines(triggers),
        '',
        html_bold('API Health'),
        build_health_block(context),
    ])
    holdings_risk_lines = build_holdings_risk_lines(context, limit=2)
    if holdings_risk_lines:
        lines.append('')
        lines.append(html_bold('持仓风险'))
        lines.extend(holdings_risk_lines)
    hot_symbols_lines = build_hot_symbols_lines(context, limit=2)
    if hot_symbols_lines:
        lines.append('')
        lines.append(html_bold('热门可交易品种'))
        lines.extend(hot_symbols_lines)
    if macro_geo_lines:
        lines.append('')
        lines.append(html_bold('宏观 / 地缘变化'))
        for index, title in enumerate(macro_geo_lines, start=1):
            lines.append(f'{index}. {html_escape(title)}')
    if us_equity_lines:
        lines.append('')
        lines.append(html_bold('美股风险情绪'))
        for index, title in enumerate(us_equity_lines, start=1):
            lines.append(f'{index}. {html_escape(title)}')
    if security_titles:
        lines.append('')
        lines.append(html_bold('安全事件'))
        for index, title in enumerate(security_titles, start=1):
            lines.append(f'{index}. {html_escape(title)}')
    if new_titles:
        lines.append('')
        lines.append(html_bold('新增持仓相关新闻'))
        for index, title in enumerate(new_titles, start=1):
            lines.append(f'{index}. {html_escape(title)}')
    if watch_titles:
        lines.append('')
        lines.append(html_bold('持续关注新闻'))
        for index, title in enumerate(watch_titles, start=1):
            lines.append(f'{index}. {html_escape(title)}')
    if not new_titles and not watch_titles:
        lines.append('')
        lines.append(html_bold('新闻摘要'))
        if news_titles:
            for index, title in enumerate(news_titles, start=1):
                lines.append(f'{index}. {html_escape(title)}')
        else:
            lines.append('1. 无高影响新闻')
    return '\n'.join(lines)


def build_user_report(report_dir: Path, pipeline_result: dict[str, Any], context: dict[str, Any], triggers: dict[str, Any]) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f'phase3_user_report_{utc_now_slug()}.md'
    holdings = ', '.join(context.get('holdings', {}).get('prioritized_symbols', [])) or '无'
    macro = context.get('macro', {}) or {}
    crypto_news = context.get('crypto_news', {}) or {}
    social = context.get('social', {}) or {}
    semantic_macro = build_semantic_macro_lines(context)
    status_ok = bool(pipeline_result.get('ok', pipeline_result.get('summary', {}).get('overall_ok')))
    new_events = crypto_news.get('new_high_impact_events') or []
    watch_events = crypto_news.get('watchlist_events') or []
    all_events = crypto_news.get('high_impact_events') or []
    security_events = crypto_news.get('security_events') or []
    lines = [
        '# Phase3 用户简报',
        '',
        '## 运行状态',
        '',
        f"- 状态: {'正常' if status_ok else '异常'}",
        '',
        '## 持仓',
        '',
        f'- 当前持仓: {holdings}',
        '',
        '## 持仓风险',
        '',
    ]
    holdings_state = context.get('holdings_state', {}) or {}
    symbol_risk = holdings_state.get('symbol_risk', []) or []
    if symbol_risk:
        for item in symbol_risk[:5]:
            symbol = str(item.get('symbol') or '').strip().upper()
            if not symbol:
                continue
            risk_state = str(item.get('risk_state') or 'unknown').strip()
            event_count = int(item.get('relevant_event_count', 0) or 0)
            social_heat = int(item.get('relevant_social_heat', 0) or 0)
            lines.append(f'- {symbol} | risk={risk_state} | events={event_count} | heat={social_heat}')
    else:
        lines.append('- 无持仓风险条目')

    lines.extend([
        '',
        '## 热门可交易品种',
        '',
    ])
    hot_symbols_state = context.get('hot_symbols_state', {}) or {}
    top_tradeable_symbols = hot_symbols_state.get('top_tradeable_symbols', []) or []
    if top_tradeable_symbols:
        for item in top_tradeable_symbols[:5]:
            symbol = str(item.get('symbol') or '').strip().upper()
            if not symbol:
                continue
            score = int(item.get('score', 0) or 0)
            sources = render_hot_symbol_sources([str(source).strip() for source in (item.get('sources') or []) if str(source).strip()])
            reasons = render_hot_symbol_reasons([str(reason).strip() for reason in (item.get('reasons') or []) if str(reason).strip()])
            lines.append(f'- {symbol} | 评分={score} | 来源={sources} | 原因={reasons}')
    else:
        lines.append('- 无热门可交易品种条目')

    lines.extend(['', '## 宏观 / 地缘变化', ''])
    lines.append(f"- Regime: {macro.get('regime', 'unknown')}")
    lines.append(f"- Regime Bias: {macro.get('regime_bias', macro.get('regime', 'unknown'))}")
    lines.append(f"- Risk State: {macro.get('risk_state', 'unknown')}")
    lines.append(f"- 地缘风险: {macro.get('geo_risk', 'unknown')}")
    lines.append(f"- 事件窗口: {'是' if macro.get('event_window') else '否'}")
    if semantic_macro['macro_geo']:
        for item in semantic_macro['macro_geo'][:5]:
            lines.append(f'- {item}')
    else:
        lines.append('- 无显著宏观 / 地缘变化')

    lines.extend(['', '## 美股风险情绪', ''])
    if semantic_macro['us_equity']:
        for item in semantic_macro['us_equity'][:5]:
            lines.append(f'- {item}')
    else:
        lines.append('- 无显著美股风险情绪变化')

    lines.extend(['', '## 新增持仓相关新闻', ''])
    if new_events:
        for index, event in enumerate(new_events[:5], start=1):
            title = str(event.get('title') or '').strip()
            impact = str(event.get('impact') or event.get('impact_level') or event.get('importance') or 'neutral').strip()
            source = str(event.get('source') or 'unknown').strip()
            lines.append(f'{index}. {title}（来源: {source}）')
            lines.append(f'   - impact: {impact}')
            lines.append(f'   - source: {source}')
    else:
        lines.append('1. 无新增持仓相关新闻')

    lines.extend(['', '## 持续关注新闻', ''])
    if watch_events:
        for index, event in enumerate(watch_events[:5], start=1):
            title = str(event.get('title') or '').strip()
            impact = str(event.get('impact') or event.get('impact_level') or event.get('importance') or 'neutral').strip()
            source = str(event.get('source') or 'unknown').strip()
            lines.append(f'{index}. {title}（来源: {source}）')
            lines.append(f'   - impact: {impact}')
            lines.append(f'   - source: {source}')
    else:
        lines.append('1. 无持续关注新闻')

    lines.extend(['', '## 安全事件', ''])
    if security_events:
        for index, event in enumerate(security_events[:5], start=1):
            title = str(event.get('title') or '').strip()
            source = str(event.get('source') or 'unknown').strip()
            state = str(event.get('state') or 'unknown').strip()
            lines.append(f'{index}. {title}')
            lines.append(f'   - state: {state}')
            lines.append(f'   - source: {source}')
    else:
        lines.append('1. 无安全事件')

    lines.extend(['', '## 重点新闻', ''])
    if all_events:
        for index, event in enumerate(all_events[:5], start=1):
            title = str(event.get('title') or '').strip()
            impact = str(event.get('impact') or event.get('impact_level') or event.get('importance') or 'neutral').strip()
            source = str(event.get('source') or 'unknown').strip()
            lines.append(f'{index}. {title}（来源: {source}）')
            lines.append(f'   - impact: {impact}')
            lines.append(f'   - source: {source}')
    else:
        lines.append('1. 无高影响新闻')
    lines.extend(['', '## Trigger / Priority', ''])
    top_symbols = ', '.join(social.get('top_discussed_symbols', [])[:5]) or '无'
    hot_ranking_symbols = ', '.join(item.get('symbol', '') for item in trigger_hot_ranking_items(triggers)) or '无'
    lines.append(f'- Top discussed symbols: {top_symbols}')
    lines.append(f'- Hot ranking symbols: {hot_ranking_symbols}')
    lines.append(f"- LLM 唤醒: {'是' if triggers.get('llm_wake_required') else '否'}")
    observe_only = ', '.join(item.get('trigger_type', '') for item in triggers.get('observe_only_triggers', [])) or '无'
    lines.append(f'- Observe only triggers: {observe_only}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def send_telegram_notifications(bot_token: str, chat_id: str, message: str, report_path: Path | None = None) -> None:
    base_url = f'https://api.telegram.org/bot{bot_token}'
    response = requests.post(
        f'{base_url}/sendMessage',
        data={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'true',
        },
        timeout=20,
    )
    response.raise_for_status()


def run_notifier() -> dict[str, Any]:
    previous_snapshot = load_notification_snapshot()
    previous_context = previous_snapshot.get('context', {}) if previous_snapshot else {}
    previous_triggers = previous_snapshot.get('triggers', {}) if previous_snapshot else {}

    pipeline_result = run_phase3_pipeline()
    context = load_context_payload()
    triggers = load_trigger_payload()
    token, chat_id = load_telegram_credentials()
    if not token or not chat_id:
        raise RuntimeError('telegram credentials are not configured')

    change_summary = build_change_summary(previous_context, previous_triggers, context, triggers)
    message = build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary=change_summary,
        report_path=None,
    )
    send_telegram_notifications(
        bot_token=token,
        chat_id=chat_id,
        message=message,
        report_path=None,
    )
    write_notification_snapshot({'context': context, 'triggers': triggers})
    return {
        'ok': True,
        'telegram_sent': True,
        'has_changes': bool(change_summary.get('has_changes')),
    }


def main() -> None:
    result = run_notifier()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
