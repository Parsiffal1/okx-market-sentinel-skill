---
name: okx-market-sentinel
description: Use this skill when an agent needs to monitor OKX-tradable markets, prioritize current holdings, collect multi-source market evidence, separate macro risk from crypto-native risk, rank what deserves attention, and produce a concise grounded summary. The skill is API-provider-agnostic: it cares about information quality and relevance, not one fixed vendor stack.
version: "1.0.0"
user-invocable: true
argument-hint: "market scan | holdings review | hot-symbol ranking | Telegram brief | event-driven risk summary"
homepage: https://github.com/Parsiffal1/okx-market-sentinel-skill
repository: https://github.com/Parsiffal1/okx-market-sentinel-skill
author: Parsiffal
license: MIT
metadata: {"openclaw": {"emoji": "📡", "tags": ["okx", "market-monitoring", "risk-sentinel", "crypto", "holdings-review", "watchlist"], "requires": {"optionalEnv": ["TIMEZONE", "DEFAULT_WATCHLIST", "DEFAULT_OUTPUT_STYLE", "DEFAULT_REPORT_CHANNEL"]}}, "hermes": {"requires_toolsets": ["web", "browser", "terminal", "file"]}}
---

# OKX Market Sentinel

## What this skill does

This skill gives an agent a reusable way to:

1. inspect current OKX-tradable market conditions
2. prioritize existing holdings before new ideas
3. combine market structure, event risk, and attention signals
4. separate macro-driven stress from crypto-native stress
5. produce a compact, operator-friendly output

This is a **monitoring and interpretation skill** built to help an agent observe, prioritize, explain, and summarize live market conditions.
Its center of gravity is judgment: what matters now, what deserves review first, and how to express that clearly.

---

## When to use it

Use this skill when the user wants any of the following:

- a market risk scan
- a holdings-first review
- a shortlist of symbols worth watching
- a concise Telegram-style or note-style summary
- a market update grounded in live information
- a second-pass explanation of why specific symbols matter now

Typical prompts:
- `Run an OKX market sentinel pass and tell me what matters now.`
- `Check my holdings first, then rank the rest of the watchlist.`
- `Search the current macro and crypto-native drivers behind today's move.`
- `Turn this into a concise Telegram brief with uncertainty notes.`

---

## Information model

This skill is **provider-agnostic**.
Do not define the workflow by vendor names.
Define it by information categories.

### Required information categories

#### 1. Market structure
Look for:
- price movement
- turnover / volume
- contract activity or open interest if available
- unusual volatility
- relative strength or weakness
- which OKX-tradable instruments are actually active

#### 2. Holdings and exposure
If the user has current positions, collect:
- current holdings or watchlist
- concentration risk
- which names deserve immediate review
- whether today’s external events directly affect those names

#### 3. Macro context
Collect any relevant evidence about:
- policy shifts
- rates / inflation / labor prints
- liquidity and risk appetite
- cross-asset weakness or strength
- geopolitical developments with market impact

#### 4. Crypto-native context
Collect any relevant evidence about:
- exchange incidents
- stablecoin stress
- security events
- protocol or token-specific shocks
- narrative rotation between sectors

#### 5. Attention and discussion signals
Use only as supporting evidence:
- abnormal discussion heat
- concentrated interest in a small set of symbols
- narrative acceleration

Do **not** treat popularity alone as decisive evidence.

---

## Core operating rules

### Rule 1 — Holdings first
If the user already has positions, those positions come before new opportunities.

### Rule 2 — Relevance beats volume
One specific, high-impact event can matter more than many generic headlines.

### Rule 3 — Signal quality beats source branding
Prefer timely, relevant, cross-checkable information.
Do not overweight a source just because it is familiar.

### Rule 4 — Explain the driver
Do not only label a result as `high risk` or `worth watching`.
Explain what is driving that conclusion.

### Rule 5 — Mark uncertainty honestly
If evidence is stale, conflicting, weak, or partial, say so explicitly.

---

## Workflow

### Phase 1 — Confirm scope
Before analyzing, identify which of these applies:
- current holdings review
- full market scan
- one sector or narrative
- event-driven follow-up
- summary formatting request

If the user gives both holdings and a general market question, treat holdings as priority.

### Phase 2 — Gather evidence
Collect evidence from any available tools or sources that can supply:
- live market structure
- current event information
- holdings context
- supporting attention signals

Allowed source forms include:
- web search
- browser inspection
- exchange or market data APIs
- databases
- MCP tools
- user-provided data
- internal adapters

Do not assume a fixed provider stack.

### Phase 3 — Sort signal categories
Separate the evidence into:
- market structure signal
- macro risk signal
- crypto-native risk signal
- holdings-specific signal
- attention / discussion signal

Then ask:
- which signals are strong?
- which are merely noisy?
- which directly affect the user’s holdings?
- which are strong enough to escalate?

### Phase 4 — Rank what matters
Produce a ranking of what deserves attention now.
A good ranking usually distinguishes:
- priority holdings at risk
- watch-only names
- hot symbols with strong confirmation
- attention-driven symbols with weak confirmation

### Phase 5 — Write the output
Output should be concise, structured, and grounded.
A good default order is:

1. market summary
2. priority holdings
3. symbols worth watching
4. driver explanation
5. confidence / uncertainty notes

Use templates from `templates/` when helpful.

---

## Output requirements

### Required output qualities
- holdings-aware when holdings exist
- evidence-based
- concise enough to read quickly
- explicit about what changed
- explicit about uncertainty
- does not overclaim causal certainty

### Good output fields
Use some subset of:
- market tone
- escalation needed: yes / no / mixed
- main drivers
- priority holdings
- watchlist / hot symbols
- why each item matters
- confidence notes

### Preferred style
- conclusion first
- evidence second
- plain language
- no raw provider jargon unless the user asked for it
- no fake precision

---

## Source-grounding rules

### Prefer
- current evidence over older summaries
- directly relevant evidence over generic commentary
- multiple confirming signals over a single isolated clue
- explicit event details over vague sentiment

### Avoid
- relying on one provider as if it were truth
- presenting unsupported causal chains as facts
- confusing attention spikes with validated market importance
- using stale summaries as live evidence

If evidence is missing, say so.
If the question cannot be answered reliably, say there is insufficient evidence.

---

## Good task patterns

### Pattern A — Holdings-first review
Use when the user gives current positions.
Output:
- which holdings need review first
- why
- whether the risk looks systemic, isolated, or uncertain

### Pattern B — Full market sweep
Use when the user wants a broad scan.
Output:
- top risk drivers
- top watchlist names
- which names are truly confirmed versus merely noisy

### Pattern C — Event-driven follow-up
Use when there is a major macro or crypto-native event.
Output:
- what changed
- which instruments are most exposed
- whether the move looks temporary, structural, or unresolved

### Pattern D — Brief formatting
Use when the user wants a Telegram-style or operator-style message.
Output:
- short bullets
- minimal noise
- direct wording
- uncertainty called out in one line

---

## Failure modes to avoid

- treating one viral discussion spike as full confirmation
- ignoring current holdings while chasing new symbols
- mixing macro stress and crypto-native stress into one vague label
- overfitting to one source just because it is easy to query
- hiding uncertainty when signals disagree
- turning this monitoring skill into trade advice

---

## Boundary conditions

If data is incomplete:
- say what is missing
- downgrade confidence
- do not invent certainty

If the user asks for execution decisions:
- provide monitoring insight, not direct trade execution instructions

If there is no reliable live information:
- say the result is limited by missing or stale evidence

---

## Related files

- `references/information-model.md`
- `references/api-agnostic-data-requirements.md`
- `references/source-grounding-rules.md`
- `references/market-monitoring-playbook.md`
- `templates/telegram-brief-template.md`
- `examples/prompts.md`
- `examples/outputs.md`
