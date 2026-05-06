# Hermes Setup Guide

## Install the skill only

Copy:

- `skills/crypto-market-sentinel/SKILL.md`
- `skills/crypto-market-sentinel/references/`
- `skills/crypto-market-sentinel/templates/`

into:

```bash
~/.hermes/skills/market-monitoring/crypto-market-sentinel/
```

## Keep the runnable reference implementation

If you also want the dashboard, notifier, tests, and source fetchers, keep the full repository checked out and run commands from repo root.

## Typical commands

```bash
python scripts/phase3_pipeline.py
python dashboard/server.py --host 127.0.0.1 --port 8765
pytest -q
```
