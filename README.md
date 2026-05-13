[English](README.md) | [中文](README.zh.md)

<div align="center">

# Market Sentinel Skill

> *Teach an agent to watch markets like an operator.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Compatible-blueviolet)](https://skills.sh)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

<br>

**A market-monitoring and judgment skill for traders.**

It helps traders search live market evidence, review holdings first, separate macro from crypto-native risk, decide whether a move should stay on watch or be treated more seriously, and turn all of that into a concise working brief.

It can also be reused by agent workflows and trading systems when needed.

[Example output](#example-output) · [Install](#install) · [What it gives](#what-it-gives) · [Trigger logic](#trigger-logic) · [How it works](#how-it-works) · [Also useful for trading agents](#also-useful-for-trading-agents) · [Read next](#read-next)

```bash
npx skills add Parsiffal1/market-sentinel-skill
```

</div>

---

## Example output

```text
Market Sentinel | Scan complete

Market tone
- market_tone: cautious
- regime_classification: macro_led
- macro_risk_level: high
- crypto_native_risk_level: medium
- action_state: escalate
- escalation_needed: yes

Main drivers
- macro repricing
- cross-asset weakness
- derivatives pressure in majors

Priority holdings
1. BTC — review_priority: highest — risk_level: high — benchmark weakness is confirmed
2. ETH — review_priority: high — risk_level: medium — derivatives activity is rising

Watchlist rank
1. SOL — confirmation_status: strong — structural confirmation plus attention
2. DOGE — confirmation_status: weak — heat is real but confirmation is incomplete

Confidence
- confidence_level: medium
- missing_evidence: better confirmation for the weaker secondary narratives
```

This is the core product idea:
**not more headlines — better judgment handoff.**

---

## What this is

Market Sentinel is a public skill repository for traders and operators who need to monitor live markets and produce a usable conclusion.

It is built first for trader-facing use.
It can also sit inside a broader trading stack when people want to reuse the same judgment layer in agent workflows.
It does not care which single exchange, broker, news provider, social feed, or MCP server you use.
It cares about whether the agent can gather enough **relevant, current, cross-checkable information** to answer questions like:

- Which current holdings deserve attention first?
- Is this move macro-led, crypto-native, mixed, or still unclear?
- Which symbols are worth monitoring now?
- What should a downstream trading agent, notifier, or researcher review next?

---

## What it gives

### 1. A holdings-first market review
When current exposure exists, the skill starts there.
It teaches the agent to review what the user already holds before chasing fresh names.

### 2. A ranked watchlist
Not a raw mover board.
A shortlist of names with reasons, confirmation quality, and upgrade logic.

### 3. Driver attribution
The skill distinguishes:
- macro pressure
- crypto-native pressure
- mixed regimes
- attention-led but weakly confirmed moves
- unresolved conditions

### 4. Reusable handoff when needed
The output is structured enough to feed:
- another trader
- a research workflow
- a Telegram notifier
- a dashboard or memory layer
- a downstream trading agent if you choose to integrate one

---

## Also useful for trading agents

This repository can also be useful when you are building a **full trading agent** rather than using it only as a trader-facing skill.

In that setup, Market Sentinel becomes a reusable market-judgment layer that helps answer:
- what matters now
- what deserves escalation
- which holdings are most exposed
- which watchlist names are structurally confirmed
- what evidence is still missing

Most stacks already know how to fetch data.
Much fewer know how to decide whether a name should stay in watch mode, be escalated for deeper review, or be handed off immediately into a fuller risk or execution workflow.

```text
live sources -> Market Sentinel -> downstream trading agent -> execution / risk / monitoring subsystems
```

In that chain, Market Sentinel provides the **judgment and prioritization layer**.
The downstream agent can then decide how to:
- adjust portfolio review priority
- tighten risk controls
- trigger a deeper strategy module
- notify a human operator
- pass only the top-ranked context into execution logic

If you want the exact lightweight contract for this handoff, read [`references/output-schema.md`](references/output-schema.md).

---

## Trigger logic

Market Sentinel should not only say *what matters*.
It should also decide what the downstream system should do next at a monitoring level.

Three action states are recommended:
- `observe` — worth monitoring, but not strong enough for deeper downstream work yet
- `escalate` — deserves deeper review by a downstream agent, risk module, or human operator
- `handoff_now` — should be forwarded immediately into a fuller trading or risk workflow

As a rule of thumb:
- holdings under direct confirmed pressure should bias toward `escalate`
- multiple aligned layers can justify `escalate` or `handoff_now`
- attention without structure should usually stay at `observe`

Read the full trigger contract in [`references/trigger-policy.md`](references/trigger-policy.md).

---

## How it works

### Step 1 — define the task
A good pass starts by deciding whether the user wants:
- a holdings review
- a market sweep
- an event follow-up
- a hot-symbol ranking
- a formatted brief

### Step 2 — gather live evidence
The skill is provider-agnostic.
It does not hard-code one vendor stack.
It works with any combination of:
- web search
- browser / document inspection
- market-data tools or APIs
- holdings or account-state inputs
- research databases
- MCP tools
- user-provided context

### Step 3 — organize evidence by category
Market Sentinel teaches the agent to think in layers:
- market structure
- holdings and exposure
- macro context
- crypto-native context
- attention signals

### Step 4 — rank what matters
The agent should separate:
- urgent holdings review
- names worth watching
- hot but weakly confirmed names
- background noise

### Step 5 — hand over a clean result
The final answer should preserve:
- ranking
- drivers
- uncertainty
- a compact downstream-ready summary

The fuller operational version lives in [`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md).

---

## Output contract

Market Sentinel intentionally uses a **lightweight semantic schema** rather than fake-precise scores.

Recommended top-level fields include:
- `task_type`
- `market_tone`
- `regime_classification`
- `macro_risk_level`
- `crypto_native_risk_level`
- `action_state`
- `escalation_needed`
- `main_drivers`
- `trigger_drivers`
- `priority_holdings`
- `watchlist_rank`
- `confirmation_status`
- `confidence_level`
- `missing_evidence`
- `downstream_handoff`

Read the full contract in [`references/output-schema.md`](references/output-schema.md).
Read the escalation rules in [`references/trigger-policy.md`](references/trigger-policy.md).

---

## Install

```bash
npx skills add Parsiffal1/market-sentinel-skill
```

Or place the repository in your local skill directory if your runtime prefers local skills.

### Runtime assumptions

This skill assumes the agent can use some combination of:
- web access
- browser or document reading
- market-data interfaces
- holdings or portfolio context
- a way to return a brief, report, or downstream handoff

No single provider stack is required.

---

## Repository structure

```text
README.md
README.zh.md
SKILL.md
references/
examples/
templates/
```

- `SKILL.md` — the main runtime contract
- `references/` — information model, grounding rules, playbook, and output schema
- `examples/` — prompts, outputs, and use cases
- `templates/` — report, brief, and watchlist templates

---

## Read next

- [`SKILL.md`](SKILL.md)
- [`references/output-schema.md`](references/output-schema.md)
- [`references/trigger-policy.md`](references/trigger-policy.md)
- [`references/information-model.md`](references/information-model.md)
- [`references/api-agnostic-data-requirements.md`](references/api-agnostic-data-requirements.md)
- [`references/source-grounding-rules.md`](references/source-grounding-rules.md)
- [`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md)
- [`examples/outputs.md`](examples/outputs.md)

---

## Boundaries

Market Sentinel is the upstream monitoring and judgment layer.
It helps answer what deserves attention, why it matters, and what should be escalated.

A fuller trading agent should still own:
- execution policy
- position sizing
- stop logic
- venue-specific safety checks
- account permission policy

If real exchange access is involved, prefer read-only credentials for the information layer.

---

## License

[MIT](LICENSE)
