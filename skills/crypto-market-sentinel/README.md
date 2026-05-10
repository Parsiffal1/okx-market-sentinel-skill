[English](README.md) | [中文](README.zh.md)

# Crypto Market Sentinel Skill

This directory contains the **reusable skill package** for the OKX Market Sentinel project.

If you only want the agent-facing guidance, start here. If you also want the runnable implementation, go back to the repository root and use the main README.

## What this skill is for

Use this skill when you want an agent to help with:

- operating the Phase3 monitoring pipeline
- auditing holdings-first risk logic
- understanding hot-symbol ranking outputs
- running or debugging the dashboard and notifier flow
- maintaining Semantic Compass phrase packs
- packaging the project into another agent environment

## Key files

- `SKILL.md` — the primary operating contract
- `references/architecture.md` — architecture and system layering
- `references/runtime-commands.md` — canonical run, test, and dashboard commands
- `templates/dashboard_settings.example.json` — dashboard settings starter template

## Relationship to the full repository

This skill package is only one part of the project. The runnable reference implementation lives at repo root:

- `scripts/`
- `dashboard/`
- `config/`
- `docs/`
- `tests/`

## Recommended reading order

1. `SKILL.md`
2. `references/runtime-commands.md`
3. `references/architecture.md`
4. repo root `README.md` / `README.zh.md` when you need full-project onboarding
