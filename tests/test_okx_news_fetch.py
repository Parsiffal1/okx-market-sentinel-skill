from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/sources/okx_news_fetch.py"
SOURCES_DIR = MODULE_PATH.parent


def load_module():
    if str(SOURCES_DIR) not in sys.path:
        sys.path.insert(0, str(SOURCES_DIR))
    spec = importlib.util.spec_from_file_location('okx_news_fetch_under_test', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_fetch_news_inputs_prefers_holdings_symbols_when_present():
    mod = load_module()

    actions = mod.build_news_fetch_actions(['BTC', 'RAVE'])

    assert actions == {
        'latest': ['news', 'latest', '--coins', 'BTC,RAVE', '--limit', '20'],
        'important': ['news', 'by-coin', '--coins', 'BTC,RAVE', '--importance', 'high', '--limit', '20'],
        'sentiment_rank': ['news', 'sentiment-rank', '--limit', '10'],
    }


def test_fetch_news_inputs_falls_back_to_global_stream_without_holdings():
    mod = load_module()

    actions = mod.build_news_fetch_actions([])

    assert actions == {
        'latest': ['news', 'latest', '--limit', '20'],
        'important': ['news', 'important', '--limit', '20'],
        'sentiment_rank': ['news', 'sentiment-rank', '--limit', '10'],
    }


def test_classify_news_risk_treats_benign_bullish_high_impact_batch_as_low():
    mod = load_module()

    payload = {
        'details': [
            {'title': 'ETF inflows continue for fifth week', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Treasury accumulation expands', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Institutional demand remains firm', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Whale accumulation continues', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Spot inflows remain positive', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Treasury reserve strategy expands', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Large holders add to positions', 'ccySentiments': [{'sentiment': 'bullish'}]},
            {'title': 'Corporate treasury buys more BTC', 'ccySentiments': [{'sentiment': 'bullish'}]},
        ]
    }

    assert mod.classify_news_risk(payload) == 'low'


def test_classify_news_risk_promotes_security_exploit_to_high_even_with_single_item():
    mod = load_module()

    payload = {
        'details': [
            {'title': 'Bridge exploit drains funds from protocol treasury', 'ccySentiments': [{'sentiment': 'bearish'}]},
        ]
    }

    assert mod.classify_news_risk(payload) == 'high'


def test_load_news_risk_terms_merges_semantic_compass_keywords(monkeypatch):
    mod = load_module()

    monkeypatch.setattr(mod, 'load_semantic_compass', lambda path=None: {
        'news_risk': {
            'severe': ['bridge exploit'],
            'benign_bullish': ['sovereign accumulation'],
            'isolated_project': ['ponzi'],
        }
    })

    terms = mod.load_news_risk_terms()

    assert 'bridge exploit' in terms['severe']
    assert 'sovereign accumulation' in terms['benign_bullish']
    assert 'ponzi' in terms['isolated_project']


def test_build_high_impact_events_normalizes_importance_instead_of_passing_sentiment_labels():
    mod = load_module()

    events = mod.build_high_impact_events([
        {'title': 'ETF inflow remains strong', 'ccySentiments': [{'sentiment': 'bullish'}], 'platformList': ['okx']},
        {'title': 'Bridge exploit drains funds from protocol treasury', 'ccySentiments': [{'sentiment': 'bearish'}], 'platformList': ['okx']},
    ])

    assert events[0]['impact'] == 'low'
    assert events[1]['impact'] == 'high'
