[English](README.md) | [中文](README.zh.md)

# Crypto Market Sentinel Skill Repo

An **OKX-first market-risk sentinel and hot-symbol monitoring skill repository**.

This repository is packaged in a way that works well for **Hermes**, **OpenClaw-style agent skills**, and users who also want the **runnable reference implementation** instead of only a prompt file.

## What this repository is

This repo combines two layers:

1. **Skill layer** — reusable operator guidance under `skills/crypto-market-sentinel/`
2. **Reference implementation** — the runnable Python project under `scripts/`, `dashboard/`, `config/`, and `tests/`

The goal is not just to describe a market-risk workflow, but to provide a reusable skill plus a concrete implementation that other users can study, copy, adapt, and run.

## Who this is for

- Users who want an **OKX-first monitoring sentinel** instead of a full trading framework
- Hermes / OpenClaw / agent users who want a **skill + runnable codebase** package
- Builders who need:
  - holdings-first monitoring
  - macro + crypto-native risk aggregation
  - hot tradeable symbol ranking
  - dashboard + Telegram reporting
  - low-token, cron-friendly workflows

## What you get

- A reusable skill entrypoint:
  - `skills/crypto-market-sentinel/SKILL.md`
- Skill-specific docs:
  - `skills/crypto-market-sentinel/README.md`
  - `skills/crypto-market-sentinel/README.zh.md`
  - `skills/crypto-market-sentinel/references/`
  - `skills/crypto-market-sentinel/templates/`
- Runnable reference code:
  - `scripts/`
  - `dashboard/`
  - `config/`
  - `tests/`
- Project docs:
  - `docs/`

## Quick start

### 1. Read the skill
Start here:

- `skills/crypto-market-sentinel/SKILL.md`

Then read the companion docs:

- `skills/crypto-market-sentinel/README.md`
- `skills/crypto-market-sentinel/references/architecture.md`
- `skills/crypto-market-sentinel/references/runtime-commands.md`

### 2. Run the reference implementation
```bash
python scripts/phase3_pipeline.py
python scripts/run_phase3_notifier.py
```

### 3. Start the dashboard
```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

## Compatibility

This repository is designed as a **skill + runnable reference implementation hybrid**.

- **Hermes**: supported as a local skill plus full reference project
- **OpenClaw-style skill layouts**: supported through the `skills/crypto-market-sentinel/` subtree and single-file frontmatter metadata
- **Other agent runtimes**: supported best through manual integration using the skill subtree plus the repo root scripts

The repository is not an in-process plugin SDK package. It is a reusable skill package with external scripts, docs, and runnable reference code.

## Dependencies

Real-world usage requires more than a single Python interpreter.

### Required
- `python`
- project Python dependencies used by the scripts

### Required for common OKX-first workflows
- `okx` CLI for OKX market / news / positions fetchers

### Required for Semantic Compass refresh
- `hermes` CLI for agent-driven phrase-pack refresh

### Optional / environment-dependent
- Telegram credentials for notifier flows
- source-specific tokens such as `OPENNEWS_TOKEN`, `TWITTER_TOKEN`, and `OPEN_TOKEN`
- locally available access to the configured upstream data providers

## Installation patterns

### Hermes
Copy or clone this repo, then place the skill directory into your Hermes skills tree.

Typical target:

```bash
~/.hermes/skills/market-monitoring/crypto-market-sentinel/
```

At minimum, copy:

- `skills/crypto-market-sentinel/SKILL.md`
- `skills/crypto-market-sentinel/references/`
- `skills/crypto-market-sentinel/templates/`

If you also want the runnable implementation, keep the full repository instead of copying only the inner skill directory.

### OpenClaw-style skill layout
This repo follows the common standalone layout used by popular skill repos:

- root README
- `skills/<skill-name>/SKILL.md`
- optional `references/`, `templates/`, and extra setup docs

That makes it easy to adapt into OpenClaw / ClawHub-style packaging later.

### Manual / other agents
Use the `skills/crypto-market-sentinel/` subtree as the skill package, and treat the repo root as reference code.

## Repository structure

```text
skills/
  crypto-market-sentinel/
    SKILL.md
    README.md
    README.zh.md
    references/
    templates/

dashboard/
scripts/
config/
tests/
docs/
README.md
README.zh.md
```

## Recommended workflow

1. Read `skills/crypto-market-sentinel/SKILL.md`
2. Review `skills/crypto-market-sentinel/references/`
3. Inspect the runnable code under `scripts/` and `dashboard/`
4. Run `pytest -q`
5. Run `python scripts/phase3_pipeline.py`
6. Adapt sources, notifier, and dashboard to your own environment

## Which file should I read first?

- I only want the skill contract → `skills/crypto-market-sentinel/SKILL.md`
- I want installation guidance → `skills/crypto-market-sentinel/README.md`
- I want architecture overview → `skills/crypto-market-sentinel/references/architecture.md`
- I want runnable commands → `skills/crypto-market-sentinel/references/runtime-commands.md`
- I want the actual implementation → `scripts/`, `dashboard/`, `config/`

## Project status and scope

This repository is **not**:

- a full auto-trading framework
- an order execution bot
- a generic quant platform

It **is**:

> an OKX-first market-risk sentinel + hot-symbol monitoring skill with a runnable reference implementation.

## Testing

```bash
pytest -q
```

## License

This repository is released under the MIT License. See `LICENSE`.
