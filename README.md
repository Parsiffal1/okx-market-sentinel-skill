[English](README.md) | [中文](README.zh.md)

<div align="center">

# Market Sentinel Skill

**Teach an agent to watch live markets like an operator: search the web, inspect holdings first, separate real risk from noise, and write a brief people can actually use.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Compatible-blueviolet)](https://skills.sh)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

</div>

---

## Why this exists

Most market-monitoring workflows stop too early.

They can fetch prices. They can pull headlines. They can show a list of movers.
But they usually fail at the part that matters:

- *Which current holdings deserve attention first?*
- *Is this move macro-driven, crypto-native, or mostly noise?*
- *Which names are worth watching right now?*
- *How do I turn all of that into a brief another operator or agent can read in seconds?*

**Market Sentinel exists to make that judgment layer reusable.**

It gives an agent a repeatable way to:
- collect live market evidence
- organize that evidence by type
- prioritize current exposure
- rank what matters now
- output a concise, grounded summary

---

## What you get

This skill teaches an agent how to produce four useful things.

### 1. A market state summary
Not just *what moved*, but what kind of regime the market is in:
- cautious
- mixed
- risk-on
- risk-off
- unresolved / conflicting

### 2. A holdings-first review
If the user already has positions, those positions come first.
The skill should identify:
- what needs immediate review
- what is only watchlist-worthy
- what looks scary but is still weakly confirmed

### 3. A hot-symbol shortlist
A ranking of names worth monitoring now, with reasons.

### 4. A readable operator brief
The final output should feel like a useful working note, not a raw dump.

---

## What the agent should pay attention to

This repository is deliberately **API-provider-agnostic**.
It does not define the workflow by vendor names.
It defines the workflow by **information categories**.

### Market structure
- price movement
- turnover / volume
- open interest or contract activity if available
- unusual volatility
- relative strength / weakness
- which instruments are actually active

### Holdings and exposure
- current positions or watchlist
- concentration risk
- direct event exposure
- names that deserve priority review right now

### Macro context
- rates, inflation, labor, liquidity, policy shifts
- cross-asset risk appetite
- geopolitical developments with real market impact

### Crypto-native context
- exchange incidents
- stablecoin stress
- security events
- token / protocol-specific shocks
- narrative rotation across sectors

### Attention signals
- sudden discussion heat
- narrative acceleration
- unusual concentration of focus on a small set of symbols

The agent may obtain these from web search, browser tools, market-data interfaces, internal systems, databases, MCP tools, or user-provided context.

---

## The core loop

This skill works best when the agent follows a simple loop:

### Step 1 — define the scope
What is the user asking for?
- a holdings review
- a market sweep
- an event-driven follow-up
- a watchlist update
- a formatted brief

### Step 2 — gather live evidence
Pull the minimum evidence needed from the relevant information categories.

### Step 3 — sort the evidence
Separate it into:
- market structure
- holdings impact
- macro drivers
- crypto-native drivers
- attention / discussion heat

### Step 4 — rank what matters
Not everything deserves equal weight.
The skill should decide:
- what is truly urgent
- what is worth watching
- what is noisy but unconfirmed

### Step 5 — write the brief
Lead with the conclusion.
Then give the reasons.
Then mark uncertainty.

A fuller operational version lives in [`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md).

---

## Typical prompts

### Holdings-first
- `Run a market sentinel pass. Review my holdings first, then tell me what else deserves attention.`
- `Reassess these positions using current market, macro, and crypto-native information.`

### Full market scan
- `Scan the market and rank the symbols worth watching now.`
- `Give me a compact market sentinel summary for the current session.`

### Event-driven follow-up
- `Search the strongest current drivers behind today's move and separate real risk from noise.`
- `Tell me whether this looks macro-led, crypto-native, or mixed.`

### Reporting
- `Turn this into a Telegram-style brief.`
- `Give me a short operator note with evidence and uncertainty clearly marked.`

More examples live in [`examples/prompts.md`](examples/prompts.md).

---

## Example output

```text
Market Sentinel | Scan complete

Market tone
- Bias: cautious
- Escalation: yes
- Main driver: macro repricing plus crypto-native stress

Priority holdings
1. BTC — elevated risk because cross-asset weakness and event clustering are aligned
2. ETH — moderate risk because derivatives activity is rising while sector sentiment is mixed

Symbols worth monitoring
1. SOL — strong activity confirmation and rising attention
2. DOGE — attention surge, but confirmation weaker than SOL

Confidence notes
- Market structure confirmation: high
- Event confirmation: medium
- Attention-only signal quality: low to medium
```

More sample outputs are in [`examples/outputs.md`](examples/outputs.md).

---

## Working style

The skill should consistently behave like this:

### Holdings before ideas
If the user already has exposure, start there.

### Relevance before volume
One precise, high-impact signal is worth more than ten vague headlines.

### Information quality before source branding
A familiar provider is not automatically better than a current, specific, cross-checkable source.

### Explanation before labels
Do not only say `high risk` or `worth watching`.
Say what is driving the conclusion.

### Honesty before certainty theater
If the evidence is mixed, say it is mixed.
If the evidence is thin, say it is thin.

---

## Recommended output shape

A strong default answer usually has this structure:

1. **Market tone**
2. **Priority holdings**
3. **Symbols worth watching**
4. **Why they matter**
5. **Confidence / uncertainty notes**

Ready-to-reuse templates live in:
- [`templates/report-template.md`](templates/report-template.md)
- [`templates/telegram-brief-template.md`](templates/telegram-brief-template.md)
- [`templates/watchlist-template.md`](templates/watchlist-template.md)

---

## Repository layout

```text
README.md
README.zh.md
SKILL.md
references/
examples/
templates/
```

- `SKILL.md` is the runtime contract
- `references/` explains the information model and grounding rules
- `examples/` shows prompts, outputs, and use cases
- `templates/` provides reusable output formats

---

## Install and use

### Install as a skill

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

Or place the repository inside your local skill directory if your agent runtime prefers local skills.

### Runtime assumptions

This skill assumes the agent can use some combination of:
- web search
- browser / document reading
- market-data tools or APIs
- holdings / account-state inputs
- messaging or reporting tools

The skill does not require one canonical provider stack.

---

## Boundaries

This skill is for monitoring, synthesis, and reporting.

It helps answer:
- what matters now
- what deserves attention first
- what looks real versus noisy

It does not replace execution controls, risk policy, or human judgment.

If real exchange access is involved, prefer read-only credentials.

---

## Read next

- [`SKILL.md`](SKILL.md)
- [`references/information-model.md`](references/information-model.md)
- [`references/api-agnostic-data-requirements.md`](references/api-agnostic-data-requirements.md)
- [`references/source-grounding-rules.md`](references/source-grounding-rules.md)
- [`examples/outputs.md`](examples/outputs.md)
