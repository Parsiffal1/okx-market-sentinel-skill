# Output Schema

Market Sentinel is most useful when its output can be consumed by both humans and downstream agents.

This schema is intentionally **lightweight**:
- stable enough for agent-to-agent handoff
- human-readable enough for direct briefs
- strict about meaning, but not falsely numeric

It is designed for use as an **upstream market-intelligence layer** for a fuller trading agent stack.
That downstream stack may include:
- portfolio review logic
- execution policy
- risk controls
- order routing
- research memory
- notifier or dashboard layers

Market Sentinel should supply the judgment-ready context that those layers consume.

---

## Design goals

A good output contract should:
1. preserve ranking
2. preserve uncertainty
3. preserve holdings-first priority
4. preserve driver attribution
5. avoid fake precision

This is why the schema uses:
- `*_level`
- `*_status`
- ranked lists
- driver arrays

Instead of hard numeric scores that the skill cannot justify consistently across venues and timeframes.

---

## Core fields

### `task_type`
What kind of pass was performed.

Recommended values:
- `holdings_review`
- `market_sweep`
- `event_followup`
- `hot_symbol_ranking`
- `brief_formatting`

### `market_tone`
The broad market state after synthesis.

Recommended values:
- `cautious`
- `mixed`
- `risk_on`
- `risk_off`
- `unresolved`

### `regime_classification`
The dominant driver regime.

Recommended values:
- `macro_led`
- `crypto_native`
- `mixed`
- `attention_led_weakly_confirmed`
- `unclear`

### `macro_risk_level`
How strong the macro pressure is in the current scan.

Recommended values:
- `low`
- `medium`
- `high`
- `unclear`

### `crypto_native_risk_level`
How strong the crypto-native pressure is in the current scan.

Recommended values:
- `low`
- `medium`
- `high`
- `unclear`

### `action_state`
The recommended next action state for the result.

Recommended values:
- `observe`
- `escalate`
- `handoff_now`
- `unclear`

See [`references/trigger-policy.md`](trigger-policy.md) for the trigger contract.

### `escalation_needed`
Whether the situation deserves deeper review or downstream action.

Recommended values:
- `yes`
- `no`
- `selective`
- `unclear`

### `main_drivers`
The top drivers behind the current conclusion.

Recommended shape:
- ordered list of short phrases

Example:
- `macro repricing`
- `exchange-linked stress`
- `stablecoin pressure`

### `trigger_drivers`
Why the scan should be upgraded, watched, or forwarded.

Recommended shape:
- ordered list of short trigger phrases

Example:
- `holdings under direct event exposure`
- `cross-asset weakness confirmed by market structure`
- `attention surge without full confirmation`

### `priority_holdings`
Ranked list of held symbols or directly relevant exposure that deserves review first.

Recommended shape per item:
- `symbol`
- `review_priority`
- `risk_level`
- `driver`
- `why_now`

### `watchlist_rank`
Ranked list of symbols worth monitoring outside the user's current priority exposure.

Recommended shape per item:
- `symbol`
- `rank_bucket`
- `confirmation_status`
- `why_now`
- `what_would_upgrade_it` (optional)

### `confirmation_status`
How well the current conclusion is confirmed.

Recommended values:
- `strong`
- `moderate`
- `weak`
- `mixed`
- `unclear`

This may be emitted once at the top level or separately per item.

### `confidence_level`
How confident the agent is in the overall synthesis.

Recommended values:
- `high`
- `medium`
- `low`
- `mixed`

### `missing_evidence`
What would most improve the judgment if it were available.

Recommended shape:
- ordered list of specific evidence gaps

Example:
- `better cross-source confirmation for the headline`
- `fresh derivatives activity for ETH`
- `clearer holdings size and concentration context`

---

## Optional field groups

### `market_structure_notes`
Use when the move itself needs brief explanation.

### `holdings_context`
Use when user exposure, concentration, or correlation is central to the conclusion.

### `attention_signal_notes`
Use when social heat or narrative spread matters, especially when it is noisy.

### `downstream_handoff`
Use when the result is explicitly meant for a fuller trading agent.

Recommended contents:
- `what_to_do_next`
- `what_not_to_assume`
- `best_input_for_next_agent`

---

## Human-readable default shape

The schema should usually appear in a readable brief like this:

1. `Market tone`
2. `Escalation`
3. `Main drivers`
4. `Priority holdings`
5. `Watchlist`
6. `Confidence / uncertainty`
7. `Missing evidence`

That means the schema is a **semantic contract**, not a demand for raw JSON in every reply.

---

## Example brief mapped to schema

```text
Market Sentinel | Scan complete

Task type
- holdings_review

Market tone
- cautious
- Regime: macro_led
- Macro risk: high
- Crypto-native risk: medium
- Escalation: yes

Main drivers
- macro repricing
- cross-asset weakness
- derivatives pressure in majors

Priority holdings
1. BTC — review_priority: highest — risk_level: high — why_now: benchmark weakness is confirmed
2. ETH — review_priority: high — risk_level: medium — why_now: derivatives activity is rising

Watchlist
1. SOL — rank_bucket: high — confirmation_status: strong — why_now: structural confirmation plus attention
2. DOGE — rank_bucket: medium — confirmation_status: weak — why_now: heat is real but confirmation is incomplete

Confidence
- confidence_level: medium
- confirmation_status: mixed

Missing evidence
- better event confirmation for secondary narratives
```

---

## Guidance for downstream trading agents

A fuller trading agent should treat Market Sentinel output as:
- **upstream judgment context**
- **ranking input**
- **risk interpretation input**
- **escalation input**

A fuller trading agent should **not** treat it as:
- an execution instruction by itself
- a substitute for position sizing rules
- a substitute for stop logic
- a substitute for venue-specific risk checks

The proper relationship is:

```text
live sources -> Market Sentinel -> downstream trading agent -> execution / risk / monitoring subsystems
```

Market Sentinel decides what deserves attention and how to frame it.
The downstream trading agent decides what to do with that information.
