from pathlib import Path


def test_dashboard_static_index_exists_and_contains_required_panels():
    path = Path(__file__).resolve().parents[1] / "dashboard/static/index.html"
    assert path.exists()
    content = path.read_text(encoding='utf-8')

    assert '市场分析看板' in content
    assert 'summary-grid' in content
    assert 'holdings-priority-panel' in content
    assert 'hot-symbols-panel' in content
    assert 'quadrant-panel' in content
    assert 'news-panel' in content
    assert 'settings-drawer' in content
    assert 'hot-symbols-table' in content
    assert 'semantic-compass-brief' in content
    assert 'refresh-semantic-compass' in content
    assert 'app.js' in content


def test_dashboard_static_prioritizes_holdings_panel_before_hot_symbols():
    content = (Path(__file__).resolve().parents[1] / "dashboard/static/index.html").read_text(encoding='utf-8')

    holdings_pos = content.index('holdings-priority-panel')
    hot_symbols_pos = content.index('hot-symbols-panel')
    assert holdings_pos < hot_symbols_pos
