[English](README.md) | [中文](README.zh.md)

# OKX Market Sentinel Skill

A production-oriented **OKX-first market monitoring and risk-sentinel skill repository** that combines a reusable agent skill package with a runnable Python reference implementation.

## Project Overview

OKX Market Sentinel is built for one job: **continuously turn scattered market, holdings, news, and social signals into a readable monitoring view that an operator or agent can act on**.

It is designed for teams or individuals who want more than a script that fetches one API endpoint, but less than a full auto-trading system. The repository focuses on:

- multi-source market context collection
- holdings-first risk inspection
- hot tradeable symbol ranking across OKX contract-tradable instruments
- Telegram-friendly reporting
- agent-skill packaging for Hermes and OpenClaw

This repository **does not** execute trades, place orders, promise returns, or provide investment advice. If you connect a real OKX account, use **read-only** credentials only.

## What problem this project solves

Most market-monitoring prototypes stop at raw data collection. They fetch prices or headlines, but they do not answer the operational questions that matter:

- *Do my current holdings need attention right now?*
- *Is today’s risk coming from macro headlines, crypto-native incidents, or exchange positioning?*
- *Which OKX-tradable symbols are actually worth watching next?*
- *How do I package the result into a message an operator can read in seconds?*

OKX Market Sentinel addresses that gap by building a structured Phase3 pipeline that aggregates source data into unified artifacts, then derives notifier-ready summaries, trigger candidates, and dashboard payloads.

## What the output looks like

A typical user-facing summary looks like this:

```text
OKX Market Sentinel | Scan complete
• Status: healthy
• Priority holdings: BTC, ETH
• Market bias: bearish
• Risk level: high
• Escalate to deeper analysis: yes
• Watch-only triggers: macro event window, holdings pressure

Risk trigger summary
Macro risk confluence     : triggered
Holdings security issue   : none
Holdings event cluster    : triggered
Escalate to deeper review : yes
Watch-only triggers       : macro event window, holdings pressure

Symbols worth watching
• Current shortlist: BTC, ETH, SOL, DOGE
• From existing holdings: BTC, ETH
• From social momentum: SOL, DOGE
• From OKX OI changes: ETH, SOL

Holdings at risk
1. BTC | risk=high | events=2 | heat=18 | drivers=macro event window, holdings event cluster
2. ETH | risk=medium | events=1 | heat=11 | drivers=open-interest change

Top tradeable symbols
1. SOL | score=82 | source=social momentum + OKX OI changes | why=high social heat; leading open-interest move
2. DOGE | score=71 | source=social momentum | why=multi-account consensus
```

## Dashboard Preview

If you want to see the product before reading the code, start here:

<img width="2560" height="6018" alt="image" src="https://github.com/user-attachments/assets/ccbe6ca9-ee04-4210-a374-395304fd04fe" />

## Core Features

- [x] **Phase3 pipeline** for source collection, context aggregation, and trigger generation
- [x] **Holdings-first risk view** that checks current exposure before surfacing new opportunities
- [x] **OKX-first hot-symbol ranking** across contract-tradable instruments, not just spot crypto coins
- [x] **Macro + crypto-native event aggregation** so exchange incidents and market structure shifts are not lost inside generic news flow
- [x] **Telegram notifier flow** for concise operational briefs
- [x] **Local dashboard** for inspecting market state, trigger state, and ranking outputs
- [x] **Reusable skill package** under `skills/crypto-market-sentinel/` for Hermes / OpenClaw style agent runtimes
- [x] **Semantic Compass maintenance flow** for updating the phrase packs that drive risk extraction and event tagging

## Tech Stack

- **Language:** Python 3.10+
- **Project shape:** runnable reference implementation + reusable agent skill package
- **Agent integration:** Hermes and OpenClaw compatible skill-directory layout
- **Decision style:** artifact-first, rules-first monitoring with optional agent-assisted semantic maintenance
- **Core libraries:** `requests`, `PyYAML`, `mcp`
- **Quality tooling:** `pytest`, `ruff`
- **External systems / APIs:** OKX data interfaces, Telegram Bot API, Jin10 MCP, crypto-news and social-source integrations configured by environment variables

## Compatibility

This repository is designed to be usable in two ways:

1. **As a runnable Python project** for local monitoring, dashboard serving, and notifier execution
2. **As a skill repository** for agent runtimes such as **Hermes** and **OpenClaw**

The reusable skill package lives under:

```text
skills/crypto-market-sentinel/
```

## Quick Start

### Environment Requirements

- Python 3.10+
- Network access for the data sources you plan to use
- Optional: OKX read-only credentials
- Optional: Telegram bot credentials
- Optional: Hermes / OpenClaw if you want to load the packaged skill directly

### Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configure API Keys

Create a local environment file:

```bash
cp .env.example .env
```

Then edit `.env` and fill in only the keys you actually need. The current pipeline usually expects **local OKX CLI/profile access** for exchange data, while these environment variables are used for notifier delivery and optional upstream integrations:

```dotenv
# OKX (keep read-only credentials if your local setup needs them)
OKX_API_KEY=
OKX_API_SECRET=
OKX_PASSPHRASE=
OKX_IS_PAPER_TRADING=true

# Telegram notifier
TELEGRAM_BOT_TOKEN=
PHASE3_NOTIFY_TELEGRAM_BOT_TOKEN=
PHASE3_NOTIFY_TELEGRAM_CHAT_ID=

# Optional upstreams
OPENNEWS_TOKEN=
TWITTER_TOKEN=
OPEN_TOKEN=
BLOCKBEATS_API_KEY=
JIN10_MCP_TOKEN=
CMC_API_KEY=
```

### Run the Project

Run the canonical Phase3 pipeline:

```bash
python scripts/phase3_pipeline.py
```

Start the local dashboard:

```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

Send a Telegram-style monitoring summary:

```bash
python scripts/run_phase3_notifier.py
```

Set `PHASE3_NOTIFY_TELEGRAM_CHAT_ID` for notifier delivery. `PHASE3_NOTIFY_TELEGRAM_BOT_TOKEN` can override `TELEGRAM_BOT_TOKEN` when you want a dedicated notifier bot.

Refresh the Semantic Compass phrase pack with an agent-assisted brief:

```bash
python scripts/refresh_semantic_compass.py --brief "Add phrases for Strait of Hormuz closure / reopening / exchange outage / stablecoin depeg"
```

### Install the Skill Only

If you only want the reusable skill package, copy it into your agent skill directory.

For Hermes:

```bash
mkdir -p ~/.hermes/skills/market-monitoring && cp -r skills/crypto-market-sentinel ~/.hermes/skills/market-monitoring/
```

For OpenClaw:

```bash
mkdir -p ~/.agents/skills/market-monitoring && cp -r skills/crypto-market-sentinel ~/.agents/skills/market-monitoring/
```

## Usage Example

### 1. Build artifacts

```bash
python scripts/phase3_pipeline.py
```

Typical outputs:

```text
context/context_cache.json
context/trigger_candidates.json
reports/phase3_report_*.md
```

### 2. Run the notifier

```bash
python scripts/run_phase3_notifier.py
```

### 3. Run tests

```bash
pytest -q
```

## Repository Structure

```text
.
├── config/                              # risk rules and semantic configuration
├── dashboard/                           # local dashboard server and static frontend
├── docs/                                # architecture, workflow, schema, and handoff docs
├── scripts/                             # Phase3 pipeline, notifier, and source fetchers
├── skills/crypto-market-sentinel/       # reusable skill package
├── tests/                               # regression and packaging tests
├── .env.example                         # local environment template
├── requirements.txt                     # runtime + dev dependencies for quick setup
├── README.md                            # English repository guide
└── README.zh.md                         # Chinese repository guide
```

## Which file should I read first?

- **I want the full runnable system** → start with `README.md`, then `scripts/phase3_pipeline.py`
- **I only want the reusable skill** → start with `skills/crypto-market-sentinel/README.md`
- **I want the architecture** → read `docs/phase3-overview.md` and `skills/crypto-market-sentinel/references/architecture.md`
- **I want common operator commands** → read `skills/crypto-market-sentinel/references/runtime-commands.md`
- **I want to inspect the dashboard entrypoint** → read `dashboard/server.py`

## Project Highlights

- **Hybrid delivery model:** not just docs, not just scripts — a real repository that can be run locally and packaged as a skill
- **Operationally readable output:** the system is optimized for short dashboards and Telegram briefs rather than raw JSON dumps alone
- **Scope discipline:** focuses on monitoring, risk surfacing, and watchlist generation without pretending to be an execution engine
- **OKX-native ranking logic:** hot-symbol discovery is grounded in OKX tradable instruments and exchange-native positioning changes
- **Agent-maintainable semantics:** the phrase-pack workflow makes semantic risk extraction maintainable over time

## Dependencies

Required or commonly used dependencies include:

- `python`
- `requests`
- `PyYAML`
- `mcp`
- `pytest`
- `ruff`
- `okx` CLI (optional, depending on your local integration path)
- `hermes` CLI (optional, for agent-assisted semantic refresh and runtime workflows)
- Telegram Bot API credentials (optional, for notifier delivery)

## Project Status and Scope

This repository currently centers on the **Phase3 sentinel pipeline** as the canonical product line:

- multi-source fetchers
- unified context cache
- trigger candidate generation
- dashboard reporting
- Telegram notifier output
- skill packaging for agent reuse

It intentionally excludes automated order execution.

## Security

- Never commit real API keys, bot tokens, or account secrets
- Use `.env` only for local development
- Prefer read-only OKX credentials
- Do not bind the dashboard to a public interface unless you add your own authentication and network controls
- Read `SECURITY.md` before public deployment

## Community

Issues and pull requests are welcome for documentation, testing, packaging, and monitoring improvements. For sensitive disclosures, follow `SECURITY.md`.

## License

MIT License
