[English](README.md) | [中文](README.zh.md)

# Crypto Market Sentinel Skill

This directory is the **skill package** for the Crypto Market Sentinel project.

If you only need the reusable skill guidance, start here. If you also want the runnable code, go back to the repository root and inspect `scripts/`, `dashboard/`, `config/`, and `tests/`.

## What this skill helps with

- holdings-first market monitoring
- OKX-first tradeable symbol ranking
- macro + crypto-native risk aggregation
- dashboard + Telegram reporting flows
- cron-friendly, low-token operation
- semantic phrase-pack maintenance via **Semantic Compass**

## Key files

- `SKILL.md` — main operator contract
- `references/architecture.md` — system design summary
- `references/runtime-commands.md` — common run / test / dashboard commands
- `templates/dashboard_settings.example.json` — starter dashboard settings

## Intended usage

Use this skill when you want to:

- adapt the sentinel to another environment
- audit risk logic and wake conditions
- deploy the dashboard and notifier stack
- package the project as an agent skill instead of a one-off script pile

## If you also want the full code

Go to repo root and inspect:

- `scripts/`
- `dashboard/`
- `config/`
- `tests/`
- `docs/`
