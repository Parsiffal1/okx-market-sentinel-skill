[English](README.md) | [中文](README.zh.md)

<div align="center">

# OKX Market Sentinel Skill

**An OKX-first, API-provider-agnostic market monitoring skill for agents that need to search, synthesize, rank, and report.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Compatible-blueviolet)](https://skills.sh)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

</div>

---

## What this skill is

OKX Market Sentinel is a **market-monitoring skill**, not a trading bot and not a dashboard product.

Its job is simple:

> help an agent turn scattered market information into a holdings-aware risk view, a watchlist, and a readable summary.

The skill is designed for workflows like:

- monitoring current holdings before they become a problem
- ranking which OKX-tradable symbols are worth attention now
- separating macro risk from crypto-native risk
- turning multi-source market noise into concise operator-facing output
- producing a brief that can be sent to chat, notes, or another agent step

This repository is now intentionally **skill-first**. It does not ship a heavy reference implementation, local dashboard, or fixed provider stack.

---

## What this skill is not

This skill does **not**:

- place trades
- manage orders
- promise profits
- require one specific API vendor
- depend on one hard-coded news, macro, or social provider

If an agent can access market data, search the web, inspect holdings, and read current event sources, the skill can be used.

---

## Core idea

Most market-monitoring setups fail in one of two ways:

1. they are too raw — lots of prices, headlines, and alerts, but no operational judgment
2. they are too narrow — they depend on one exchange view, one news feed, or one sentiment source

OKX Market Sentinel solves that by giving the agent a reusable workflow:

1. gather market structure information
2. gather macro and crypto-native events
3. check current holdings first
4. score what matters now
5. output the result in a compact, explainable format

The important thing is that the skill is **information-oriented, not provider-oriented**.

---

## What information the agent should collect

The skill cares about **information categories**, not vendor names.

### 1. Market structure
- price change
- volume / turnover
- open interest or contract activity if available
- unusual volatility or relative strength
- top movers among OKX-tradable instruments

### 2. Holdings and exposure
- current positions or watchlist
- exposure concentration
- position-specific event risk
- which names deserve priority review right now

### 3. Macro context
- rates, inflation, labor, liquidity, policy shifts
- cross-asset risk appetite
- major geopolitical shocks that can reprice crypto and leveraged instruments

### 4. Crypto-native context
- exchange incidents
- stablecoin stress
- security events
- token / protocol-specific blowups
- narrative rotation between sectors

### 5. Social and attention signals
- discussion heat
- sudden narrative acceleration
- unusual concentration of attention on a small set of symbols

The agent may obtain these from web search, exchange interfaces, data APIs, internal tools, databases, MCP servers, or human-provided notes.

---

## What the skill outputs

A good run should usually produce some combination of the following:

### A. Risk summary
- current market tone
- what changed since the last scan
- whether risk is rising, stable, or mixed

### B. Holdings-first review
- which current holdings need immediate attention
- what event or market behavior is driving that concern
- whether the issue looks systemic, isolated, or uncertain

### C. Hot-symbol shortlist
- the most relevant OKX-tradable names to monitor now
- why they appear on the list
- which signals support the ranking

### D. Operator brief
A short output suitable for chat or notes, for example:

```text
OKX Market Sentinel | Scan complete

Market tone
- Bias: cautious
- Escalation: yes
- Main driver: macro event window + crypto-native stress

Priority holdings
1. BTC — risk elevated due to cross-asset weakness and event clustering
2. ETH — watch for derivatives pressure and sector spillover

Symbols worth monitoring
1. SOL — rising heat + strong contract activity
2. DOGE — attention surge without equally strong structural confirmation

Confidence notes
- Macro signal strength: high
- Crypto-native event confirmation: medium
- Social signal reliability: mixed
```

---

## Typical prompts

### General market scan
- `Run an OKX market sentinel pass and give me a concise risk summary.`
- `Look across OKX-tradable contracts and tell me what deserves attention right now.`

### Holdings-first scan
- `Reassess my current holdings first, then rank what else is worth monitoring.`
- `Given these holdings, tell me which positions face the highest immediate risk and why.`

### Event-driven scan
- `Use current macro and crypto-native developments to tell me whether this is a risk-on or risk-off window for OKX contracts.`
- `Search for the main drivers behind today’s strongest moves and separate noise from real risk.`

### Reporting
- `Turn this scan into a Telegram-style brief.`
- `Give me a watchlist plus evidence, with uncertainty clearly marked.`

More examples live in [`examples/prompts.md`](examples/prompts.md).

---

## How the skill should think

### Principle 1 — holdings before ideas
If the user already has positions, those positions get priority over new opportunities.

### Principle 2 — information beats source branding
The skill should not care whether a macro headline came from one provider or another. It should care whether the information is timely, specific, and cross-checkable.

### Principle 3 — event importance is not the same as social popularity
A widely discussed topic can still be weak evidence. A low-volume but high-impact operational event can matter much more.

### Principle 4 — explain the driver, not just the label
Do not say only `risk high`. Say what is actually driving the risk: macro repricing, exchange stress, open-interest shift, security shock, or uncertain social heat.

### Principle 5 — mark uncertainty honestly
If evidence is partial, conflicting, stale, or weak, the output should say so.

---

## Skill workflow

A strong execution usually looks like this:

1. confirm scope
   - holdings? watchlist? full market? one sector?
2. collect current market structure data
3. collect macro and crypto-native events
4. collect supporting discussion / attention signals if useful
5. compare signal quality across categories
6. identify the few items that actually matter
7. produce a readable summary with evidence and uncertainty notes

A more detailed version is in [`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md).

---

## Source grounding expectations

The skill should prefer:

- current information over stale information
- multiple confirming signals over one isolated signal
- directly relevant evidence over generic commentary
- exchange / market / event evidence over vague sentiment summaries

The agent should avoid:

- over-trusting one provider
- presenting unsupported causal claims as facts
- confusing correlated noise with a real trigger
- treating old summaries as if they were live market evidence

Detailed grounding rules are in [`references/source-grounding-rules.md`](references/source-grounding-rules.md).

---

## File layout

```text
README.md
README.zh.md
SKILL.md
references/
examples/
templates/
```

- `SKILL.md` is the main runtime contract
- `references/` explains the information model and decision rules
- `examples/` shows prompts, outputs, and use cases
- `templates/` gives reusable output formats

---

## Installation and usage

### Install as a skill

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

Or copy the repository into your agent skill directory if your runtime expects local skills.

### Runtime assumptions

This skill assumes the agent can use some combination of:

- web search
- browser or document reading tools
- market-data tools or APIs
- holdings / account state inputs
- messaging or reporting output tools

It does **not** require one canonical provider stack.

---

## Safety boundary

This skill helps with monitoring and interpretation.
It does **not** replace human judgment, execution controls, or risk management policy.

Use read-only credentials when connecting real exchange data.
Never interpret the output as guaranteed profit or personalized investment advice.

---

## Read next

- [`SKILL.md`](SKILL.md)
- [`references/information-model.md`](references/information-model.md)
- [`references/api-agnostic-data-requirements.md`](references/api-agnostic-data-requirements.md)
- [`examples/outputs.md`](examples/outputs.md)
