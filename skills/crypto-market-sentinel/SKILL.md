---
name: crypto-market-sentinel
description: Operate an OKX-first market risk sentinel with holdings-first monitoring, hot-symbol ranking, dashboard reporting, Telegram notifier flows, and agent-refreshable semantic phrase packs. Use when the user wants to run, adapt, review, harden, or package this project as a reusable agent skill.
version: "0.1.0"
argument-hint: "audit risk logic | run dashboard | tune semantic compass | package for another deployment"
user-invocable: true
homepage: https://github.com/Parsiffal1/okx-market-sentinel-skill
repository: https://github.com/Parsiffal1/okx-market-sentinel-skill
author: Parsiffal
license: UNLICENSED
metadata:
  openclaw:
    emoji: "📡"
    tags:
      - market-monitoring
      - okx
      - crypto
      - dashboard
      - telegram
      - risk-management
      - semantic-compass
    requires:
      bins:
        - python
      optionalEnv:
        - OKX credentials
        - TELEGRAM_BOT_TOKEN
        - OPENNEWS_TOKEN
        - TWITTER_TOKEN
        - OPEN_TOKEN
---

# Crypto Market Sentinel

Use this skill when the task involves **operating, adapting, auditing, or packaging** the Crypto Market Sentinel project.

This project is an **OKX-first market risk sentinel and hot-symbol monitoring upstream**, not a full trading framework.

## What this repository contains

- reusable skill package under `skills/crypto-market-sentinel/`
- runnable reference implementation under repo root:
  - `scripts/`
  - `dashboard/`
  - `config/`
  - `tests/`
  - `docs/`

## When to use this skill

Use it for tasks like:

- run the canonical pipeline
- audit risk-state logic and extreme/wake conditions
- tune macro / geo / news risk semantics
- refresh Semantic Compass phrase packs
- deploy or debug the dashboard
- prepare Telegram notifier reporting
- package or publish the repository as a reusable agent skill

## Core mental model

The system has five layers:

1. **source fetchers**
   - `scripts/sources/*.py`
2. **context aggregation**
   - `scripts/build_context_cache.py`
3. **trigger generation**
   - `scripts/build_triggers.py`
4. **reporting / dashboard / notifier**
   - `dashboard/`
   - `scripts/run_phase3_notifier.py`
5. **semantic phrase-pack maintenance**
   - `scripts/semantic_compass.py`
   - `config/semantic_compass.json`

Do not treat this as a single-script project. Problems usually live at one of those layers.

## First files to inspect

If the user asks about:

- market risk / geo risk / news risk:
  - `scripts/build_context_cache.py`
  - `scripts/sources/jin10_fetch.py`
  - `scripts/sources/okx_news_fetch.py`
  - `config/semantic_compass.json`
- trigger logic:
  - `scripts/build_triggers.py`
- dashboard:
  - `dashboard/server.py`
  - `dashboard/dashboard_adapter.py`
  - `dashboard/static/`
- packaging / publishing:
  - `README.md`
  - `README.zh.md`
  - `skills/crypto-market-sentinel/`

## Canonical commands

### Run the pipeline
```bash
python scripts/phase3_pipeline.py
```

### Run notifier
```bash
python scripts/run_phase3_notifier.py
```

### Rebuild only core artifacts
```bash
python scripts/build_context_cache.py
python scripts/build_triggers.py
```

### Start dashboard
```bash
python dashboard/server.py --host 0.0.0.0 --port 8765
```

### Refresh Semantic Compass with an agent brief
```bash
python scripts/refresh_semantic_compass.py --brief "补充霍尔木兹海峡关闭 / 恢复通航 / 稳定币脱锚 / 交易所宕机等常见表述"
```

### Run tests
```bash
pytest -q
```

## Semantic Compass rules

`Semantic Compass` is the project’s **agent-refreshable semantic phrase pack**.

Files:
- `config/semantic_compass.json`
- `scripts/semantic_compass.py`
- `scripts/refresh_semantic_compass.py`

It feeds:
- `jin10_fetch.py` geo-risk phrase matching
- `okx_news_fetch.py` news-risk phrase matching
- dashboard settings / refresh UI metadata

When tuning semantics:
- keep shock phrases narrow and high-confidence
- keep de-escalation phrases explicit
- separate systemic market risk from isolated project incidents
- never silently overwrite broken JSON; validate after refresh

## Packaging guidance

When publishing this project as a skill repo:
- keep `skills/crypto-market-sentinel/SKILL.md` as the main entrypoint
- keep root README focused on repo-level onboarding
- keep runnable reference code at repo root
- exclude runtime artifacts like `context/`, `reports/`, `.env`, `__pycache__/`
- document clearly that this is a skill + reference implementation hybrid

## Common pitfalls

- confusing `0.0.0.0` bind address with a public URL
- treating sentiment labels as event importance
- letting broad background geo terms escalate directly to `extreme`
- allowing dashboard settings APIs to overwrite internal runtime state
- shipping cached runtime artifacts or secrets in a public repo

## Verification checklist

Before saying the project is healthy:
- `pytest -q` passes
- dashboard API returns valid JSON
- pipeline success/failure signals are trustworthy
- Semantic Compass refresh validates written JSON
- no `.env`, runtime caches, or reports are packaged for release

## Related docs

- `references/architecture.md`
- `references/runtime-commands.md`
- repo root `README.md`
- repo root `README.zh.md`
