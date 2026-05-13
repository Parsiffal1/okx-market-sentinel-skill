# Trigger and Escalation Policy

Market Sentinel is not only a summarizer.
It is first a trader-facing monitoring and judgment skill.
When needed, it can also act as an escalation layer inside a broader workflow.

A good pass should decide not just *what is happening*, but also:
- what only deserves watching
- what deserves deeper review
- what deserves immediate downstream handoff

This document defines that contract.

---

## Design goals

The trigger policy should:
1. preserve holdings-first priority
2. distinguish monitoring from escalation
3. make trigger reasons explicit
4. stay portable across exchanges and providers
5. avoid pretending to be an execution engine

---

## Three action states

### 1. `observe`
Use this when something is worth monitoring but does not yet justify deeper downstream work.

Typical profile:
- one layer is active, but confirmation is incomplete
- attention is rising, but market structure is weak
- there is no direct holdings impact yet
- evidence is interesting, but not decisive

### 2. `escalate`
Use this when the scan deserves deeper review by a downstream agent, risk module, or human operator.

Typical profile:
- multiple layers align
- a held symbol is under direct pressure
- market structure confirms the concern
- a meaningful macro or crypto-native event is active

### 3. `handoff_now`
Use this when the result should be forwarded immediately into a fuller trading or risk workflow.

Typical profile:
- current holdings are directly exposed
- confirmation is strong enough that delay is costly
- the issue is not only informational but operationally time-sensitive
- a downstream agent needs the result now for portfolio review, risk tightening, or human notification

---

## Holdings review priority

When holdings exist, they outrank external watchlist names.

Recommended levels:

### `highest`
Use when:
- the holding is directly exposed to the active driver
- the signal is confirmed by structure or multiple evidence layers
- the user would plausibly change risk posture after review

### `high`
Use when:
- the holding is relevant to the current regime
- confirmation is meaningful but not complete
- the symbol deserves review before external names

### `medium`
Use when:
- the holding is relevant, but not under the strongest current pressure
- confirmation is partial or indirect

### `low`
Use when:
- the holding is not central to the current event
- it can stay in the output, but should not dominate attention

---

## Trigger-driver grading

`trigger_drivers` should not be a random list.
They should explain *why* the action state changed.

Recommended grades:

### Grade A — direct escalation drivers
These are strong enough to support `escalate` or `handoff_now` when paired with confirmation.

Examples:
- direct holdings exposure to active event
- broad market-structure weakness in held majors
- high-confidence macro repricing with cross-asset confirmation
- exchange / stablecoin / security stress with clear spillover

### Grade B — meaningful but incomplete drivers
These usually support `observe` or `escalate`, depending on confirmation quality.

Examples:
- sector rotation with moderate confirmation
- derivatives pressure without fully clear spot confirmation
- one strong event source plus one weaker confirming source

### Grade C — attention or weak-context drivers
These should rarely justify escalation by themselves.

Examples:
- social heat spike without structure
- narrative spread without clear price / volume confirmation
- one-off headline with unclear downstream impact

---

## Escalation heuristics

### Escalate if holdings + confirmation align
If a current holding is hit by an active driver and the move is confirmed structurally, default toward `escalate`.

### Escalate if multiple layers point the same way
If macro, crypto-native, and market-structure signals all point in one direction, do not leave the result at `observe` unless the evidence is stale or contradictory.

### Stay at observe if heat outruns structure
If the main excitement comes from attention signals and confirmation is weak, default toward `observe`.

### Use handoff_now sparingly
`handoff_now` is for cases where the downstream agent truly needs immediate review.
It should feel rare and justified, not like a louder synonym for `escalate`.

---

## Recommended fields for trigger-aware outputs

At top level:
- `action_state`
- `escalation_needed`
- `trigger_drivers`
- `confidence_level`
- `missing_evidence`

Per holding:
- `review_priority`
- `risk_level`
- `driver`
- `why_now`

Per watchlist item:
- `rank_bucket`
- `confirmation_status`
- `what_would_upgrade_it`

---

## Example trigger-aware brief

```text
Market Sentinel.skill | Trigger-aware scan

Action state
- action_state: escalate
- escalation_needed: yes

Trigger drivers
- direct holdings exposure to macro repricing
- cross-asset weakness confirmed in benchmark majors
- secondary crypto-native stress increasing spillover risk

Priority holdings
1. BTC — review_priority: highest — risk_level: high — why_now: benchmark weakness is broadly confirmed
2. ETH — review_priority: high — risk_level: medium — why_now: derivatives pressure is building

Watchlist rank
1. SOL — rank_bucket: high — confirmation_status: strong — why_now: leadership remains intact
2. DOGE — rank_bucket: attention_only — confirmation_status: weak — what_would_upgrade_it: clearer structure confirmation
```

---

## Boundary

The trigger policy tells the downstream system **what deserves attention next**.
It does not tell the downstream system:
- exact order size
- exact stop placement
- exact execution venue choice
- final portfolio action

That remains the job of the fuller trading agent or human operator.
