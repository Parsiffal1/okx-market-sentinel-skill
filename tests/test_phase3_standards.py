from __future__ import annotations

import ast
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def test_phase3_standards_doc_exists_and_covers_required_sections():
    standards_path = BASE_DIR / 'docs' / 'phase3-standards.md'

    assert standards_path.exists()
    content = standards_path.read_text(encoding='utf-8')

    assert '# Phase3 Standards' in content
    assert 'Canonical workflow' in content
    assert 'Source fetcher template' in content
    assert 'Stdout JSON summary schema' in content
    assert 'Raw cache schema' in content


def test_phase3_project_has_root_formatting_config_files():
    editorconfig_path = BASE_DIR / '.editorconfig'
    pyproject_path = BASE_DIR / 'pyproject.toml'

    assert editorconfig_path.exists()
    assert pyproject_path.exists()

    editorconfig = editorconfig_path.read_text(encoding='utf-8')
    pyproject = pyproject_path.read_text(encoding='utf-8')

    assert 'charset = utf-8' in editorconfig
    assert 'indent_style = space' in editorconfig
    assert 'indent_size = 4' in editorconfig
    assert '[tool.ruff]' in pyproject
    assert '[tool.ruff.format]' in pyproject


def test_phase3_core_scripts_have_module_docstrings():
    script_paths = [
        BASE_DIR / 'scripts' / 'phase3_pipeline.py',
        BASE_DIR / 'scripts' / 'build_context_cache.py',
        BASE_DIR / 'scripts' / 'build_triggers.py',
        BASE_DIR / 'scripts' / 'sources' / '_common.py',
        BASE_DIR / 'scripts' / 'sources' / 'okx_positions_fetch.py',
        BASE_DIR / 'scripts' / 'sources' / 'blockbeats_fetch.py',
        BASE_DIR / 'scripts' / 'sources' / 'okx_news_fetch.py',
        BASE_DIR / 'scripts' / 'sources' / 'opennews_fetch.py',
        BASE_DIR / 'scripts' / 'sources' / 'opentwitter_fetch.py',
        BASE_DIR / 'scripts' / 'sources' / 'jin10_fetch.py',
    ]

    for path in script_paths:
        module = ast.parse(path.read_text(encoding='utf-8'))
        assert ast.get_docstring(module), f'module docstring missing: {path}'
