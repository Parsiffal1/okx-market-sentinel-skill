from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/jin10_fetch.py"


def load_module():
    spec = importlib.util.spec_from_file_location('jin10_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_dt_treats_calendar_pub_time_as_beijing_time():
    mod = load_module()
    parsed = mod.parse_dt('2026-04-22 22:30')
    assert parsed is not None
    assert parsed.isoformat() == '2026-04-22T14:30:00+00:00'


def test_build_macro_payload_sets_geo_risk_and_split_event_window_flags():
    mod = load_module()
    payload = mod.build_macro_payload(
        flash_items=[
            {
                'content': '美国袭击伊朗核设施，油价飙升，市场避险情绪急剧升温。',
                'time': '2026-04-22T12:00:00+08:00',
            }
        ],
        news_items=[
            {
                'title': '中东冲突升级引发避险交易',
                'introduction': '黄金与原油同步走高。',
            }
        ],
        calendar_items=[
            {
                'country': '美国',
                'title': 'PCE物价指数',
                'importance': 4,
                'pub_time': '2026-04-23 06:30',
            },
            {
                'country': '美国',
                'title': 'CPI',
                'importance': 3,
                'pub_time': '2026-04-22 20:00',
            },
        ],
        now=datetime(2026, 4, 22, 14, 47, tzinfo=timezone.utc),
    )

    assert payload['geo_risk'] == 'high'
    assert payload['event_window'] is True
    assert payload['event_pre_release'] is True
    assert payload['event_recent_release'] is False
    assert payload['macro_summary'] == ['美国袭击伊朗核设施，油价飙升，市场避险情绪急剧升温。']


def test_classify_geo_risk_treats_persistent_conflict_background_as_medium_until_new_shock():
    mod = load_module()
    texts = [
        '特朗普称最快周五重启与伊朗谈判。',
        '伊朗外交部表示尚未决定是否参加新一轮谈判。',
        '霍尔木兹海峡局势依旧紧张，但暂无新的封锁措施。',
    ]

    assert mod.classify_geo_risk(texts) == 'medium'


def test_load_macro_rules_merges_semantic_compass_keywords(monkeypatch):
    mod = load_module()

    monkeypatch.setattr(mod, 'load_semantic_compass', lambda path=None: {
        'geo_risk': {
            'deescalation': ['恢复通航'],
            'shock': ['关闭霍尔木兹海峡'],
            'anchors': ['阿曼湾'],
        }
    })

    rules = mod.load_macro_rules()

    assert '恢复通航' in rules['geo_risk_deescalation_keywords']
    assert '关闭霍尔木兹海峡' in rules['geo_risk_shock_keywords']
    assert '阿曼湾' in rules['geo_risk_anchor_keywords']



def test_build_macro_payload_marks_recent_release_window():
    mod = load_module()
    payload = mod.build_macro_payload(
        flash_items=[],
        news_items=[],
        calendar_items=[
            {
                'country': '美国',
                'title': 'CPI',
                'importance': 3,
                'pub_time': '2026-04-22 22:30',
            }
        ],
        now=datetime(2026, 4, 22, 14, 50, tzinfo=timezone.utc),
    )

    assert payload['event_window'] is True
    assert payload['event_pre_release'] is False
    assert payload['event_recent_release'] is True


def test_build_macro_payload_falls_back_to_news_for_geo_risk_when_flash_has_no_geo_signal():
    mod = load_module()
    payload = mod.build_macro_payload(
        flash_items=[
            {
                'content': '凯投宏观：日本央行最早可能在6月加息。',
                'time': '2026-04-24T09:39:05+08:00',
            }
        ],
        news_items=[
            {
                'title': '伊朗发视频炫耀控制海峡、挑战美军优势，快艇“蜂群战术”加剧霍尔木兹航运威胁',
                'introduction': '专家警告海峡运输与区域安全风险同步上升。',
            }
        ],
        calendar_items=[],
        now=datetime(2026, 4, 24, 2, 0, tzinfo=timezone.utc),
    )

    assert payload['geo_risk'] == 'medium'


def test_detect_event_window_respects_rule_overrides():
    mod = load_module()
    payload = mod.detect_event_window(
        calendar_items=[
            {
                'country': '美国',
                'title': 'PCE物价指数',
                'importance': 4,
                'pub_time': '2026-04-23 05:00',
            }
        ],
        now=datetime(2026, 4, 22, 14, 0, tzinfo=timezone.utc),
        rules={
            'event_window_crypto_high_relevance_keywords': ['PCE'],
            'event_window_hours_before': 6,
            'event_window_hours_after': 1,
        },
    )

    assert payload['event_window'] is False
    assert payload['event_pre_release'] is False
    assert payload['event_recent_release'] is False


def test_detect_event_window_ignores_non_us_calendar_items_even_when_keywords_match():
    mod = load_module()
    payload = mod.detect_event_window(
        calendar_items=[
            {
                'country': '英国',
                'title': 'CPI',
                'importance': 4,
                'pub_time': '2026-04-23 05:00',
            },
            {
                'country': '欧元区',
                'title': 'PCE',
                'importance': 4,
                'pub_time': '2026-04-23 05:00',
            },
        ],
        now=datetime(2026, 4, 22, 23, 30, tzinfo=timezone.utc),
    )

    assert payload == {
        'event_window': False,
        'event_pre_release': False,
        'event_recent_release': False,
    }


def test_summarize_items_filters_out_low_relevance_macro_noise():
    mod = load_module()
    rules = {
        'macro_summary_relevance_keywords': ['特朗普', '美联储', '霍尔木兹', '原油', 'CPI', '非农'],
        'macro_summary_exclude_keywords': ['A股', '杭州', '小米', '恒生科技指数', '人行广东省分行', '国内期货', '纽约期银'],
    }

    summary = mod.summarize_items(
        flash_items=[
            {'content': '【杭州：一季度生产总值6109亿 同比增长5.6%】'},
            {'content': 'A股半导体材料概念开盘活跃，怡达股份、百川股份涨停。'},
            {'content': '特朗普称将继续评估伊朗停火安排，霍尔木兹局势仍紧张。'},
            {'content': 'WTI原油短线拉升，市场担忧中东供应冲击。'},
            {'content': '【人行广东省分行：3月广东金融机构新发放贷款利率平均为3.06%】'},
            {'content': '早盘收盘，国内期货主力合约涨跌互现，SC原油涨超3%。'},
            {'content': '纽约期银日内跌超3.00%，现报75.62美元/盎司。'},
        ],
        news_items=[
            {'title': '白宫高官：若沃什未能及时上任，支持鲍威尔暂留', 'introduction': '美联储路径仍是焦点。'},
            {'title': '小米MiMo-V2.5系列模型开启公测', 'introduction': 'AI模型公测。'},
        ],
        rules=rules,
        limit=5,
    )

    assert summary == [
        '特朗普称将继续评估伊朗停火安排，霍尔木兹局势仍紧张。',
        'WTI原油短线拉升，市场担忧中东供应冲击。',
        '白宫高官：若沃什未能及时上任，支持鲍威尔暂留 - 美联储路径仍是焦点。',
    ]


def test_merge_macro_items_prefers_search_hits_and_deduplicates_noise():
    mod = load_module()
    rules = {
        'macro_summary_relevance_keywords': ['特朗普', '美联储', '霍尔木兹', '原油', 'CPI', '非农'],
        'macro_summary_exclude_keywords': ['A股', '杭州', 'HKMA', '离岸人民币同业拆息', 'HIBOR', '每日热门ETF要闻汇总'],
    }

    flash_items = mod.merge_macro_items(
        primary_items=[
            {'content': '特朗普称将继续评估伊朗停火安排，霍尔木兹局势仍紧张。', 'time': '2026-04-23T12:00:00+08:00'},
            {'content': 'WTI原油短线拉升，市场担忧中东供应冲击。', 'time': '2026-04-23T11:59:00+08:00'},
        ],
        supplemental_items=[
            {'content': '【离岸人民币同业拆息利率多数上行，HKMA日间回购协议流动性被用逾四成】', 'time': '2026-04-23T11:58:00+08:00'},
            {'content': '特朗普称将继续评估伊朗停火安排，霍尔木兹局势仍紧张。', 'time': '2026-04-23T12:00:00+08:00'},
            {'content': 'A股半导体材料概念开盘活跃，怡达股份、百川股份涨停。', 'time': '2026-04-23T09:31:00+08:00'},
            {'content': '金十数据整理：每日热门ETF要闻汇总（2026-04-23）\n1. 特朗普、白宫均否认就停火延长设最后期限。\n2. 台积电展示新一代芯片技术。', 'time': '2026-04-23T09:16:33+08:00'},
        ],
        text_getter=lambda item: item.get('content', ''),
        rules=rules,
    )

    assert flash_items == [
        {'content': '特朗普称将继续评估伊朗停火安排，霍尔木兹局势仍紧张。', 'time': '2026-04-23T12:00:00+08:00'},
        {'content': 'WTI原油短线拉升，市场担忧中东供应冲击。', 'time': '2026-04-23T11:59:00+08:00'},
    ]


@pytest.mark.asyncio
async def test_run_fetch_writes_ok_cache_from_mcp_results(tmp_path):
    mod = load_module()
    written = {}

    async def fake_fetcher(token: str):
        assert token == 'token-123'
        return {
            'flash_items': [
                {'content': '以色列与伊朗冲突升级，原油上涨。', 'time': '2026-04-22T12:00:00+08:00'}
            ],
            'news_items': [
                {'title': '地缘政治风险升温', 'introduction': '市场风险偏好下降。'}
            ],
            'calendar_items': [
                {
                    'country': '美国',
                    'title': '非农就业',
                    'importance': 3,
                    'pub_time': '2026-04-22 22:30',
                }
            ],
        }

    def fake_write_raw_cache(filename: str, source: str, status: str, data: dict, error: str | None = None):
        written.update({
            'filename': filename,
            'source': source,
            'status': status,
            'data': data,
            'error': error,
        })
        path = tmp_path / filename
        path.write_text('ok', encoding='utf-8')
        return path

    result = await mod.run_fetch(
        token='token-123',
        fetcher=fake_fetcher,
        write_cache=fake_write_raw_cache,
        now=datetime(2026, 4, 22, 14, 0, tzinfo=timezone.utc),
    )

    assert result['status'] == 'ok'
    assert written['source'] == 'jin10'
    assert written['status'] == 'ok'
    assert written['data']['macro']['geo_risk'] == 'medium'
    assert written['data']['macro']['event_window'] is True
    assert written['data']['macro']['event_pre_release'] is True
    assert written['data']['macro']['event_recent_release'] is False


@pytest.mark.asyncio
async def test_fetch_from_mcp_uses_list_endpoints_only_without_active_search(monkeypatch):
    mod = load_module()
    called_tools: list[str] = []

    class DummyResult:
        def __init__(self, payload):
            self.structuredContent = payload
            self.content = []

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def initialize(self):
            return None

        async def call_tool(self, name, params):
            called_tools.append(name)
            if name == 'list_flash':
                return DummyResult({'data': {'items': [{'content': '特朗普称将继续评估伊朗停火安排。'}], 'next_cursor': None, 'has_more': False}})
            if name == 'list_news':
                return DummyResult({'data': {'items': [{'title': '白宫高官表态', 'introduction': '美联储路径仍是焦点。'}], 'next_cursor': None, 'has_more': False}})
            if name == 'list_calendar':
                return DummyResult({'data': {'items': []}})
            raise AssertionError(f'unexpected tool call: {name}')

    class DummyStream:
        async def __aenter__(self):
            return (object(), object(), object())

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(mod, 'streamablehttp_client', lambda *args, **kwargs: DummyStream())
    monkeypatch.setattr(mod, 'ClientSession', lambda *args, **kwargs: DummySession())
    monkeypatch.setattr(mod, 'load_macro_rules', lambda: {
        'macro_search_keywords': ['特朗普', '白宫'],
        'list_flash_max_pages': 1,
        'list_news_max_pages': 1,
        'search_news_max_pages': 1,
        'macro_summary_relevance_keywords': ['特朗普', '白宫', '美联储'],
        'macro_summary_exclude_keywords': [],
    })

    fetched = await mod.fetch_from_mcp('token-123')

    assert [tool for tool in called_tools if tool.startswith('search_')] == []
    assert called_tools == ['list_flash', 'list_news', 'list_calendar']
    assert len(fetched['flash_items']) == 1
    assert len(fetched['news_items']) == 1


@pytest.mark.asyncio
async def test_run_fetch_requires_token():
    mod = load_module()

    with pytest.raises(ValueError):
        await mod.run_fetch(token='')



def test_classify_geo_risk_deescalation_and_open_transit_stays_low():
    mod = load_module()
    texts = [
        '美军：伊朗的袭击尚未达到重启大规模作战行动的门槛。',
        '美防长称两艘商船及美驱逐舰顺利通过霍尔木兹海峡，航运未受干扰。',
        '美防长：将确保霍尔木兹海峡通航自由。',
    ]

    assert mod.classify_geo_risk(texts) == 'low'


def test_build_macro_payload_prefers_news_shock_over_background_flash_tension():
    mod = load_module()
    payload = mod.build_macro_payload(
        flash_items=[
            {'content': '霍尔木兹海峡局势依旧紧张，但暂无新的封锁措施。', 'time': '2026-04-24T09:39:05+08:00'},
        ],
        news_items=[
            {'title': '伊朗宣布关闭霍尔木兹海峡，商船暂停通行', 'introduction': '航运中断风险急升。'},
        ],
        calendar_items=[],
        now=datetime(2026, 4, 24, 2, 0, tzinfo=timezone.utc),
    )

    assert payload['geo_risk'] == 'high'
    assert payload['geo_risk_has_shock'] is True
