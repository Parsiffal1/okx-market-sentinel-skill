from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import copy

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/run_phase3_notifier.py"
SCRIPTS_DIR = MODULE_PATH.parent


def load_module():
    import sys

    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location('run_phase3_notifier_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_telegram_credentials_reads_token_from_hermes_env_and_chat_id_from_config(tmp_path, monkeypatch):
    mod = load_module()
    hermes_env = tmp_path / '.env'
    hermes_env.write_text('TELEGRAM_BOT_TOKEN=test-bot-token\n', encoding='utf-8')
    hermes_config = tmp_path / 'config.yaml'
    hermes_config.write_text("TELEGRAM_HOME_CHANNEL: '7874568756'\n", encoding='utf-8')
    monkeypatch.setattr(mod, 'HERMES_ENV_FILE', hermes_env)
    monkeypatch.setattr(mod, 'HERMES_CONFIG_FILE', hermes_config)

    token, chat_id = mod.load_telegram_credentials()

    assert token == 'test-bot-token'
    assert chat_id == '7874568756'


def test_load_telegram_credentials_prefers_phase3_specific_bot_and_chat(tmp_path, monkeypatch):
    mod = load_module()
    hermes_env = tmp_path / '.env'
    hermes_env.write_text(
        'TELEGRAM_BOT_TOKEN=main-bot\n'
        'PHASE3_NOTIFY_TELEGRAM_BOT_TOKEN=phase3-bot\n'
        'PHASE3_NOTIFY_TELEGRAM_CHAT_ID=123456\n',
        encoding='utf-8',
    )
    hermes_config = tmp_path / 'config.yaml'
    hermes_config.write_text("TELEGRAM_HOME_CHANNEL: '7874568756'\n", encoding='utf-8')
    monkeypatch.setattr(mod, 'HERMES_ENV_FILE', hermes_env)
    monkeypatch.setattr(mod, 'HERMES_CONFIG_FILE', hermes_config)

    token, chat_id = mod.load_telegram_credentials()

    assert token == 'phase3-bot'
    assert chat_id == '123456'


def test_run_phase3_pipeline_raises_when_payload_reports_failure(monkeypatch):
    mod = load_module()

    class Result:
        returncode = 0
        stdout = json.dumps({'ok': False, 'summary': {'overall_ok': False}})
        stderr = ''

    monkeypatch.setattr(mod.subprocess, 'run', lambda *args, **kwargs: Result())

    try:
        mod.run_phase3_pipeline()
        raised = None
    except RuntimeError as exc:
        raised = exc

    assert raised is not None
    assert 'overall_ok' in str(raised)


def test_build_notification_message_summarizes_phase3_result():
    mod = load_module()
    pipeline_result = {
        'summary': {'overall_ok': True},
        'report_path': str(Path(__file__).resolve().parents[1] / "reports" / "phase3_report_test.md"),
    }
    context = {
        'holdings': {'prioritized_symbols': ['BTC']},
        'macro': {
            'regime': 'bearish',
            'regime_bias': 'bearish',
            'risk_state': 'high',
            'geo_risk': 'high',
            'event_window': True,
        },
        'health': {'jin10': 'ok', 'cmc': 'ok', 'moss_xsignal': 'ok', 'blockbeats': 'partial', 'okx_positions': 'ok'},
        'crypto_news': {
            'high_impact_events': [
                {'title': 'Strategy adds more BTC', 'source': 'blockbeats'},
                {'title': 'Funding squeeze risk rises', 'source': 'okx_news'},
            ],
            'new_high_impact_events': [
                {'title': 'Strategy adds more BTC', 'source': 'blockbeats'},
            ],
            'watchlist_events': [
                {'title': 'Funding squeeze risk rises', 'source': 'okx_news'},
            ],
            'security_events': [],
        },
    }
    triggers = {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [{'trigger_type': 'macro_risk_confluence'}],
        'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'ETH'}],
    }
    change_summary = {'has_changes': True, 'lines': ['## 状态变化', '- 新增重点新闻：Strategy adds more BTC']}

    message = mod.build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary=change_summary,
        report_path=str(Path(__file__).resolve().parents[1] / "reports" / "phase3_user_report_test.md"),
    )

    assert '<b>OKX 市场哨兵｜运行完成</b>' in message
    assert '• 持仓: <code>BTC</code>' in message
    assert '• 方向偏置: <code>bearish</code>' in message
    assert '• 风险等级: <code>high</code>' in message
    assert '• LLM 唤醒: <code>否</code>' in message
    assert '<b>状态变化</b>' not in message
    assert '新增重点新闻：Strategy adds more BTC' not in message
    assert '<b>Trigger 判定</b>' in message
    assert '<pre>宏观四因子共振 :' in message
    assert '<b>热度排名</b>' in message
    assert '• 当前列表: <code>BTC, ETH</code>' in message
    assert '<b>API Health</b>' in message
    assert 'moss_xsignal:ok' in message
    assert '<b>新增持仓相关新闻</b>' in message
    assert '1. Strategy adds more BTC（来源: blockbeats）' in message
    assert '<b>持续关注新闻</b>' in message
    assert '1. Funding squeeze risk rises（来源: okx_news）' in message


def test_build_user_report_creates_human_readable_markdown_without_json_escapes(tmp_path):
    mod = load_module()
    pipeline_result = {
        'summary': {'overall_ok': True},
        'report_path': str(tmp_path / 'phase3_report_raw.md'),
    }
    context = {
        'holdings': {'prioritized_symbols': ['BTC']},
        'macro': {
            'regime': 'bearish',
            'regime_bias': 'bearish',
            'risk_state': 'high',
            'geo_risk': 'high',
            'event_window': True,
            'macro_summary': ['特朗普表示没有时间表，也不着急。'],
            'summary_buckets': {
                'geo': ['霍尔木兹海峡航运几陷停滞'],
                'macro_financial': ['美国10年期国债收益率升至4.6%，美元指数走强'],
                'us_equity_sentiment': ['纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱'],
            },
        },
        'crypto_news': {
            'high_impact_events': [
                {'title': 'Strategy adds more BTC', 'impact': 'bullish', 'source': 'techflowpost'},
                {'title': 'Funding squeeze risk rises', 'impact': 'neutral', 'source': 'blockbeats'},
            ],
            'new_high_impact_events': [
                {'title': 'Strategy adds more BTC', 'impact': 'bullish', 'source': 'techflowpost'},
            ],
            'watchlist_events': [
                {'title': 'Funding squeeze risk rises', 'impact': 'neutral', 'source': 'blockbeats'},
            ],
            'security_events': [
                {'title': 'Bridge exploit drains funds from protocol treasury', 'source': 'okx_news', 'state': 'live_exploit'},
            ],
        },
        'social': {'top_discussed_symbols': ['BTC', 'ETH']},
    }
    triggers = {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [{'trigger_type': 'macro_risk_confluence'}],
        'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'ETH'}],
    }

    report_path = mod.build_user_report(tmp_path, pipeline_result, context, triggers)
    content = report_path.read_text(encoding='utf-8')

    assert report_path.name.startswith('phase3_user_report_')
    assert '## 持仓' in content
    assert '## 宏观 / 地缘变化' in content
    assert '## 美股风险情绪' in content
    assert '## 安全事件' in content
    assert '## Trigger / Priority' in content
    assert '霍尔木兹海峡航运几陷停滞' in content
    assert '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱' in content
    assert 'Bridge exploit drains funds from protocol treasury' in content
    assert 'Strategy adds more BTC' in content
    assert 'Funding squeeze risk rises' in content
    assert '\\n' not in content



def test_build_user_report_includes_holdings_risk_and_hot_symbols_sections(tmp_path):
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}}
    context = {
        'holdings': {'prioritized_symbols': ['BTC', 'RAVE']},
        'holdings_state': {
            'has_positions': True,
            'prioritized_symbols': ['BTC', 'RAVE'],
            'symbol_risk': [
                {'symbol': 'BTC', 'risk_state': 'high', 'relevant_event_count': 2, 'relevant_social_heat': 92000, 'macro_alignment': 'bearish', 'reasons': ['held_symbol_event_cluster']},
                {'symbol': 'RAVE', 'risk_state': 'medium', 'relevant_event_count': 1, 'relevant_social_heat': 21000, 'macro_alignment': 'bearish', 'reasons': ['global_market_risk_medium']},
            ],
        },
        'hot_symbols_state': {
            'top_tradeable_symbols': [
                {'symbol': 'BTC', 'score': 160, 'rank': 1, 'sources': ['holding', 'social'], 'reasons': ['existing_holding', 'high_social_heat']},
                {'symbol': 'RAVE', 'score': 132, 'rank': 2, 'sources': ['holding', 'cmc'], 'reasons': ['existing_holding', 'cmc_trending_symbol']},
            ]
        },
        'macro': {'summary_buckets': {'geo': [], 'macro_financial': [], 'us_equity_sentiment': []}},
        'crypto_news': {'high_impact_events': [], 'new_high_impact_events': [], 'watchlist_events': [], 'security_events': []},
        'social': {'top_discussed_symbols': ['BTC', 'RAVE']},
    }
    triggers = {'llm_wake_required': False, 'llm_wake_triggers': [], 'observe_only_triggers': [], 'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'RAVE'}]}

    report_path = mod.build_user_report(tmp_path, pipeline_result, context, triggers)
    content = report_path.read_text(encoding='utf-8')

    assert '## 持仓风险' in content
    assert 'BTC | risk=high | events=2 | heat=92000' in content
    assert 'RAVE | risk=medium | events=1 | heat=21000' in content
    assert '## 热门可交易品种' in content
    assert 'BTC | 评分=160 | 来源=持仓优先 + 社媒热议 | 原因=持仓标的；社媒高热' in content
    assert 'RAVE | 评分=132 | 来源=持仓优先 + CMC趋势 | 原因=持仓标的；CMC趋势上榜' in content



def test_build_notification_message_uses_semantic_sections_when_available():
    mod = load_module()
    pipeline_result = {
        'summary': {'overall_ok': True},
        'report_path': str(Path(__file__).resolve().parents[1] / "reports" / "phase3_report_test.md"),
    }
    context = {
        'holdings': {'prioritized_symbols': ['BTC']},
        'macro': {
            'regime': 'bearish',
            'regime_bias': 'bearish',
            'risk_state': 'high',
            'geo_risk': 'high',
            'event_window': True,
            'summary_buckets': {
                'geo': ['霍尔木兹海峡航运几陷停滞'],
                'macro_financial': ['美国10年期国债收益率升至4.6%，美元指数走强'],
                'us_equity_sentiment': ['纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱'],
            },
        },
        'health': {'jin10': 'ok', 'blockbeats': 'ok', 'cmc': 'ok', 'moss_xsignal': 'ok', 'okx_news': 'ok', 'opennews': 'ok', 'opentwitter': 'ok', 'okx_positions': 'ok'},
        'crypto_news': {
            'news_risk': 'high',
            'high_impact_events': [
                {'title': 'Bridge exploit drains funds from protocol treasury'},
                {'title': 'Funding squeeze risk rises'},
            ],
            'new_high_impact_events': [
                {'title': 'Bridge exploit drains funds from protocol treasury'},
            ],
            'watchlist_events': [
                {'title': 'Funding squeeze risk rises'},
            ],
            'security_events': [
                {'title': 'Bridge exploit drains funds from protocol treasury', 'source': 'okx_news', 'state': 'live_exploit'},
            ],
        },
    }
    triggers = {
        'llm_wake_required': True,
        'llm_wake_triggers': [{'trigger_type': 'held_symbol_security_event'}],
        'observe_only_triggers': [],
        'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'ETH'}],
    }
    change_summary = {
        'has_changes': True,
        'lines': ['## 状态变化', '- 地缘风险：`medium` → `high`', '- 事件窗口：`否` → `是`'],
    }

    message = mod.build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary=change_summary,
        report_path=str(Path(__file__).resolve().parents[1] / "reports" / "phase3_user_report_test.md"),
    )

    assert '<b>宏观 / 地缘变化</b>' in message
    assert '<b>美股风险情绪</b>' in message
    assert '<b>安全事件</b>' in message
    assert '<b>状态变化</b>' not in message
    assert '地缘风险：`medium` → `high`' not in message
    assert '<b>Trigger 判定</b>' in message
    assert '<b>热度排名</b>' in message
    assert '霍尔木兹海峡航运几陷停滞' in message
    assert '纳斯达克指数盘初跌超1.2%，QQQ与SPY同步走弱' in message
    assert message.count('Bridge exploit drains funds from protocol treasury') == 1
    assert '<b>API Health</b>' in message
    assert 'moss_xsignal:ok' in message



def test_build_notification_message_highlights_holdings_risk_and_hot_symbols_state():
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}}
    context = {
        'holdings': {'prioritized_symbols': ['BTC', 'RAVE']},
        'holdings_state': {
            'has_positions': True,
            'prioritized_symbols': ['BTC', 'RAVE'],
            'symbol_risk': [
                {
                    'symbol': 'BTC',
                    'risk_state': 'high',
                    'relevant_event_count': 2,
                    'relevant_social_heat': 92000,
                    'macro_alignment': 'bearish',
                    'reasons': ['held_symbol_event_cluster', 'held_symbol_social_heat_elevated'],
                },
                {
                    'symbol': 'RAVE',
                    'risk_state': 'medium',
                    'relevant_event_count': 1,
                    'relevant_social_heat': 21000,
                    'macro_alignment': 'bearish',
                    'reasons': ['global_market_risk_medium'],
                },
            ],
        },
        'hot_symbols_state': {
            'updated_at': '2026-05-05T10:10:00+00:00',
            'top_tradeable_symbols': [
                {
                    'symbol': 'BTC',
                    'score': 160,
                    'rank': 1,
                    'sources': ['holding', 'social'],
                    'reasons': ['existing_holding', 'high_social_heat', 'multi_account_discussion'],
                },
                {
                    'symbol': 'RAVE',
                    'score': 132,
                    'rank': 2,
                    'sources': ['holding', 'cmc'],
                    'reasons': ['existing_holding', 'cmc_trending_symbol'],
                },
            ],
        },
        'macro': {
            'regime': 'bearish',
            'regime_bias': 'bearish',
            'risk_state': 'high',
            'geo_risk': 'medium',
            'event_window': False,
            'summary_buckets': {'geo': [], 'macro_financial': [], 'us_equity_sentiment': []},
        },
        'health': {'jin10': 'ok', 'blockbeats': 'ok', 'cmc': 'ok', 'moss_xsignal': 'ok', 'okx_news': 'ok', 'okx_positions': 'ok', 'opennews': 'ok', 'opentwitter': 'ok'},
        'crypto_news': {'high_impact_events': [], 'new_high_impact_events': [], 'watchlist_events': [], 'security_events': []},
    }
    triggers = {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [],
        'hot_symbols_ranking': [{'symbol': 'BTC', 'source': 'holding'}, {'symbol': 'RAVE', 'source': 'holding'}],
    }

    message = mod.build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary={'has_changes': True, 'lines': ['## 状态变化', '- 持仓风险有变化']},
        report_path=None,
    )

    assert '<b>持仓风险</b>' in message
    assert '1. BTC ｜ risk=high ｜ events=2 ｜ heat=92000' in message
    assert '2. RAVE ｜ risk=medium ｜ events=1 ｜ heat=21000' in message
    assert '<b>热门可交易品种</b>' in message
    assert '1. BTC ｜ 评分=160 ｜ 来源=持仓优先 + 社媒热议 ｜ 原因=持仓标的；社媒高热；多账户共识' in message
    assert '2. RAVE ｜ 评分=132 ｜ 来源=持仓优先 + CMC趋势 ｜ 原因=持仓标的；CMC趋势上榜' in message





def test_build_user_report_makes_hot_symbols_and_news_human_readable(tmp_path):
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}}
    context = {
        'holdings': {'prioritized_symbols': ['BTC']},
        'hot_symbols_state': {
            'top_tradeable_symbols': [
                {
                    'symbol': 'BTC',
                    'score': 160,
                    'rank': 1,
                    'sources': ['holding', 'social'],
                    'reasons': ['existing_holding', 'high_social_heat', 'multi_account_discussion'],
                },
            ]
        },
        'macro': {'summary_buckets': {'geo': [], 'macro_financial': [], 'us_equity_sentiment': []}},
        'crypto_news': {
            'high_impact_events': [{'title': 'Strategy adds more BTC', 'impact': 'bullish', 'source': 'blockbeats'}],
            'new_high_impact_events': [{'title': 'Strategy adds more BTC', 'impact': 'bullish', 'source': 'blockbeats'}],
            'watchlist_events': [],
            'security_events': [],
        },
        'social': {'top_discussed_symbols': ['BTC']},
    }
    triggers = {'llm_wake_required': False, 'llm_wake_triggers': [], 'observe_only_triggers': [], 'hot_symbols_ranking': [{'symbol': 'BTC'}]}

    report_path = mod.build_user_report(tmp_path, pipeline_result, context, triggers)
    content = report_path.read_text(encoding='utf-8')

    assert 'BTC | 评分=160 | 来源=持仓优先 + 社媒热议 | 原因=持仓标的；社媒高热；多账户共识' in content
    assert '1. Strategy adds more BTC（来源: blockbeats）' in content

def test_build_notification_message_shows_okx_market_source_in_health_and_hot_ranking_breakdown():
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}}
    context = {
        'holdings': {'prioritized_symbols': []},
        'macro': {'summary_buckets': {'geo': [], 'macro_financial': [], 'us_equity_sentiment': []}},
        'crypto_news': {'high_impact_events': [], 'new_high_impact_events': [], 'watchlist_events': [], 'security_events': []},
        'health': {'jin10': 'ok', 'blockbeats': 'ok', 'cmc': 'ok', 'moss_xsignal': 'ok', 'okx_market': 'ok', 'okx_news': 'ok', 'okx_positions': 'ok', 'opennews': 'ok', 'opentwitter': 'ok'},
    }
    triggers = {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [],
        'hot_symbols_ranking': [
            {'symbol': 'AAPL', 'source': 'okx_top_gainers', 'priority': 'medium', 'reasons': ['okx_top_gainer_24h']},
            {'symbol': 'GC', 'source': 'okx_oi_change', 'priority': 'medium', 'reasons': ['okx_oi_price_up_quadrant', 'okx_oi_change_leader']},
        ],
    }

    message = mod.build_notification_message(pipeline_result, context, triggers, change_summary={'has_changes': True, 'lines': ['ok']}, report_path=None)

    assert 'okx_market:ok' in message
    assert '• OKX涨幅榜: <code>AAPL</code>' in message
    assert '• OKX持仓异动: <code>GC</code>' in message



def test_build_notification_message_never_mentions_report_path_in_message_only_mode():
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}, 'report_path': str(Path(__file__).resolve().parents[1] / "reports" / "phase3_report_test.md")}
    context = {
        'holdings': {'prioritized_symbols': ['ETH', 'BTC']},
        'macro': {'summary_buckets': {'geo': ['伊朗称已制定针对美方及其盟友的反击目标清单'], 'macro_financial': [], 'us_equity_sentiment': []}},
        'crypto_news': {'high_impact_events': [], 'new_high_impact_events': [], 'watchlist_events': [], 'security_events': []},
    }
    triggers = {'llm_wake_required': False, 'llm_wake_triggers': [], 'observe_only_triggers': [], 'hot_symbols_ranking': [{'symbol': 'BTC'}]}

    message = mod.build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary={'has_changes': True, 'lines': ['首次运行：已完成。']},
        report_path=str(Path(__file__).resolve().parents[1] / "reports" / "phase3_user_report_test.md"),
    )

    assert '报告:' not in message
    assert 'phase3_user_report' not in message
    assert 'phase3_report' not in message



def test_build_notification_message_stays_compact_in_changed_mode():
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}}
    context = {
        'holdings': {'prioritized_symbols': ['MASK', 'ETH', 'BTC']},
        'macro': {
            'regime': 'bearish',
            'regime_bias': 'bearish',
            'risk_state': 'high',
            'geo_risk': 'medium',
            'event_window': False,
            'summary_buckets': {
                'geo': ['伊朗秀「快艇蜂群战术」叫板美军：霍尔木兹海峡航运风险急剧上升'],
                'macro_financial': [],
                'us_equity_sentiment': ['特朗普「操盘」美股：涨跌全看政策，40年来最强市场影响力'],
            },
        },
        'health': {'jin10': 'ok', 'blockbeats': 'ok', 'cmc': 'ok', 'moss_xsignal': 'ok', 'okx_news': 'ok', 'okx_positions': 'ok', 'opennews': 'ok', 'opentwitter': 'ok'},
        'crypto_news': {
            'news_risk': 'high',
            'high_impact_events': [{'title': 'KelpDAO黑客完成「洗币」，近2000枚BTC转出'}],
            'new_high_impact_events': [{'title': 'KelpDAO黑客完成「洗币」，近2000枚BTC转出'}],
            'watchlist_events': [{'title': 'Analyst: CEX had a net outflow of nearly 100,000 BTC on the 30th'}],
            'security_events': [{'title': 'KelpDAO黑客完成「洗币」，近2000枚BTC转出', 'state': 'postmortem'}],
        },
    }
    triggers = {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [],
        'hot_symbols_ranking': [{'symbol': 'BTC'}],
    }

    message = mod.build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary={'has_changes': True, 'lines': ['## 状态变化', '- 地缘风险：`unknown` → `medium`']},
        report_path=None,
    )

    assert message.count('KelpDAO黑客完成「洗币」，近2000枚BTC转出') == 1
    assert len(message.splitlines()) <= 42


def test_build_notification_message_stays_compact_in_no_change_mode():
    mod = load_module()
    pipeline_result = {'summary': {'overall_ok': True}}
    context = {
        'holdings': {'prioritized_symbols': ['ETH', 'BTC']},
        'macro': {'summary_buckets': {'geo': ['伊朗称已制定针对美方及其盟友的反击目标清单'], 'macro_financial': [], 'us_equity_sentiment': []}},
        'crypto_news': {'high_impact_events': [], 'new_high_impact_events': [], 'watchlist_events': [], 'security_events': []},
    }
    triggers = {
        'llm_wake_required': False,
        'llm_wake_triggers': [],
        'observe_only_triggers': [],
        'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'ETH'}],
    }

    message = mod.build_notification_message(
        pipeline_result,
        context,
        triggers,
        change_summary={'has_changes': False, 'lines': ['OKX 市场哨兵｜本轮无重要变化']},
        report_path=str(Path(__file__).resolve().parents[1] / "reports" / "phase3_user_report_test.md"),
    )

    assert '<b>OKX 市场哨兵｜本轮无重要变化</b>' in message
    assert '宏观/地缘变化:' not in message
    assert '美股风险情绪:' not in message
    assert '安全事件:' not in message
    assert len(message.splitlines()) <= 5


def test_build_change_summary_formats_macro_deltas_as_readable_bullets():
    mod = load_module()
    previous_context = {
        'holdings': {'prioritized_symbols': ['BTC']},
        'macro': {'regime': 'bearish', 'geo_risk': 'unknown', 'event_window': True},
        'crypto_news': {
            'high_impact_events': [
                {'title': 'Strategy adds more BTC'},
                {'title': 'Funding squeeze risk rises'},
            ]
        },
    }
    previous_triggers = {
        'llm_wake_required': False,
        'observe_only_triggers': [{'trigger_type': 'macro_risk_confluence'}],
        'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'ETH'}],
    }
    current_context = copy.deepcopy(previous_context)
    current_context['holdings']['prioritized_symbols'] = ['ETH', 'BTC']
    current_context['macro']['geo_risk'] = 'medium'
    current_context['macro']['event_window'] = False
    current_context['crypto_news']['high_impact_events'] = [
        {'title': 'Strategy adds more BTC'},
        {'title': 'Bitmine buys 100,000 ETH'},
    ]
    current_triggers = copy.deepcopy(previous_triggers)
    current_triggers['hot_symbols_ranking'] = [{'symbol': 'BTC'}, {'symbol': 'ETH'}, {'symbol': 'SOL'}]

    summary = mod.build_change_summary(previous_context, previous_triggers, current_context, current_triggers)

    assert summary['has_changes'] is True
    assert '## 状态变化' in summary['lines']
    assert '- 持仓：`BTC` → `ETH, BTC`' in summary['lines']
    assert '- 地缘风险：`unknown` → `medium`' in summary['lines']
    assert '- 事件窗口：`是` → `否`' in summary['lines']
    assert '- 新增重点新闻：Bitmine buys 100,000 ETH' in summary['lines']
    assert '- 热度排名：`BTC, ETH` → `BTC, ETH, SOL`' in summary['lines']


def test_build_change_summary_returns_no_change_status_when_key_fields_match():
    mod = load_module()
    context = {
        'holdings': {'prioritized_symbols': ['ETH', 'BTC']},
        'macro': {'regime': 'bearish', 'geo_risk': 'high', 'event_window': True},
        'crypto_news': {
            'high_impact_events': [
                {'title': 'Strategy adds more BTC'},
                {'title': 'Bitmine buys 100,000 ETH'},
            ]
        },
    }
    triggers = {
        'llm_wake_required': False,
        'observe_only_triggers': [{'trigger_type': 'macro_risk_confluence'}],
        'hot_symbols_ranking': [{'symbol': 'BTC'}, {'symbol': 'ETH'}, {'symbol': 'SOL'}],
    }

    summary = mod.build_change_summary(context, triggers, copy.deepcopy(context), copy.deepcopy(triggers))

    assert summary['has_changes'] is False
    assert summary['lines'] == ['哨兵：本轮无重要变化，无新增重要新闻，继续观察市场。']


def test_send_telegram_notifications_posts_summary_only_in_message_mode(tmp_path, monkeypatch):
    mod = load_module()
    report_path = tmp_path / 'report.md'
    report_path.write_text('# report', encoding='utf-8')
    calls = []

    class FakeResponse:
        status_code = 200
        text = 'ok'

        def raise_for_status(self):
            return None

    def fake_post(url, data=None, files=None, timeout=None):
        calls.append({'url': url, 'data': data, 'files': files, 'timeout': timeout})
        return FakeResponse()

    monkeypatch.setattr(mod.requests, 'post', fake_post)

    mod.send_telegram_notifications(
        bot_token='bot-token',
        chat_id='7874568756',
        message='phase3 ok',
        report_path=report_path,
    )

    assert len(calls) == 1
    assert calls[0]['url'].endswith('/sendMessage')
    assert calls[0]['data']['chat_id'] == '7874568756'
    assert calls[0]['data']['text'] == 'phase3 ok'
    assert calls[0]['data']['parse_mode'] == 'HTML'
    assert calls[0]['data']['disable_web_page_preview'] == 'true'
    assert calls[0]['files'] is None


def test_send_telegram_notifications_skips_document_when_report_path_is_none(monkeypatch):
    mod = load_module()
    calls = []

    class FakeResponse:
        status_code = 200
        text = 'ok'

        def raise_for_status(self):
            return None

    def fake_post(url, data=None, files=None, timeout=None):
        calls.append({'url': url, 'data': data, 'files': files, 'timeout': timeout})
        return FakeResponse()

    monkeypatch.setattr(mod.requests, 'post', fake_post)

    mod.send_telegram_notifications(
        bot_token='bot-token',
        chat_id='7874568756',
        message='phase3 ok',
        report_path=None,
    )

    assert len(calls) == 1
    assert calls[0]['url'].endswith('/sendMessage')


def test_run_notifier_returns_sent_status(monkeypatch, tmp_path):
    mod = load_module()
    pipeline_output = {
        'ok': True,
        'report_path': str(tmp_path / 'phase3_report_test.md'),
        'summary': {'overall_ok': True},
    }
    (tmp_path / 'phase3_report_test.md').write_text('# report', encoding='utf-8')
    context = {'holdings': {'prioritized_symbols': ['BTC']}, 'crypto_news': {'high_impact_events': []}}
    triggers = {'llm_wake_required': False, 'llm_wake_triggers': [], 'observe_only_triggers': [], 'hot_symbols_ranking': []}

    monkeypatch.setattr(mod, 'run_phase3_pipeline', lambda: pipeline_output)
    monkeypatch.setattr(mod, 'load_context_payload', lambda path=None: context)
    monkeypatch.setattr(mod, 'load_trigger_payload', lambda path=None: triggers)
    monkeypatch.setattr(mod, 'load_telegram_credentials', lambda: ('bot-token', '7874568756'))
    sent = []
    monkeypatch.setattr(mod, 'send_telegram_notifications', lambda **kwargs: sent.append(kwargs))

    result = mod.run_notifier()

    assert result['ok'] is True
    assert result['telegram_sent'] is True
    assert 'report_path' not in result
    assert sent[0]['report_path'] is None

