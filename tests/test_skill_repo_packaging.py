from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "crypto-market-sentinel" / "SKILL.md"
README_PATH = REPO_ROOT / "README.md"
SECURITY_PATH = REPO_ROOT / "SECURITY.md"
LICENSE_PATH = REPO_ROOT / "LICENSE"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_skill_frontmatter_uses_openclaw_compatible_single_line_metadata_and_declares_real_bins():
    text = read_text(SKILL_PATH)
    assert 'metadata: {"openclaw":' in text
    assert '"bins": ["python", "okx", "hermes"]' in text
    assert '"optionalEnv": ["TELEGRAM_BOT_TOKEN", "OPENNEWS_TOKEN", "TWITTER_TOKEN", "OPEN_TOKEN"]' in text
    assert 'license: MIT' in text


def test_repository_has_license_and_security_policy():
    assert LICENSE_PATH.exists()
    assert SECURITY_PATH.exists()
    security = read_text(SECURITY_PATH)
    assert 'Security Policy' in security
    assert 'Do not open public GitHub issues for secrets' in security


def test_readme_explains_skill_compatibility_dependencies_and_safe_dashboard_binding():
    text = read_text(README_PATH)
    assert 'Compatibility' in text
    assert 'Hermes' in text and 'OpenClaw' in text
    assert 'Dependencies' in text
    assert '`python`' in text
    assert '`okx` CLI' in text
    assert '`hermes` CLI' in text
    assert '--host 127.0.0.1' in text
    assert 'Telegram' in text
