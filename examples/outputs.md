# Example Outputs

## Example 1 — holdings-first brief

```text
Market Sentinel.skill | Scan complete

Task type
- holdings_review

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
3. SOL — review_priority: medium — risk_level: medium — attention is strong but confirmation is less stable than BTC

Watchlist rank
1. SOL — rank_bucket: high — confirmation_status: strong — structural confirmation plus attention
2. DOGE — rank_bucket: medium — confirmation_status: weak — attention is real but confirmation remains incomplete

Confidence
- confidence_level: medium
- confirmation_status: mixed
- missing_evidence: stronger confirmation for the weaker secondary narratives
```

### Why this is a good output
- starts with current holdings
- keeps a stable upstream-ready structure
- explains why BTC is above ETH and SOL
- keeps uncertainty visible instead of pretending full certainty

---

## Example 2 — full market sweep

```text
Market Sentinel.skill | Watchlist update

Task type
- market_sweep

Market tone
- market_tone: mixed
- regime_classification: mixed
- macro_risk_level: medium
- crypto_native_risk_level: medium
- action_state: observe
- escalation_needed: selective

Main drivers
- macro risk window remains open
- crypto-native stress is concentrated rather than market-wide

Watchlist rank
1. BTC — rank_bucket: high — confirmation_status: strong — benchmark weakness still matters most
2. SOL — rank_bucket: high — confirmation_status: strong — leadership with structural confirmation
3. ETH — rank_bucket: medium — confirmation_status: moderate — important because of derivatives spillover
4. DOGE — rank_bucket: attention_only — confirmation_status: weak — heat is high, but confirmation remains incomplete

Confidence
- confidence_level: medium
- confirmation_status: moderate
- missing_evidence: cleaner confirmation for the attention-led names
```

### Why this is a good output
- distinguishes broad market tone from symbol ranking
- does not over-upgrade DOGE just because it is noisy
- stays usable for both humans and downstream agents

---

## Example 3 — event-driven follow-up

```text
Market Sentinel.skill | Event follow-up

Task type
- event_followup

Market tone
- market_tone: cautious
- regime_classification: mixed
- action_state: escalate
- escalation_needed: yes

Main drivers
- cross-asset weakness increased the baseline risk tone
- a crypto-native incident added pressure to exchange-linked narratives
- attention surged faster than broad structural confirmation in meme-related names

Priority exposures
1. BTC — review_priority: highest — risk_level: high — still the cleanest benchmark for the macro leg
2. ETH — review_priority: high — risk_level: medium — exposed to both derivatives pressure and sector spillover
3. DOGE — review_priority: low — risk_level: low to medium — heat is real, but confirmation remains weak

Confidence
- confidence_level: medium
- confirmation_status: mixed
- missing_evidence: stronger structural confirmation for the attention spike
```

### Why this is a good output
- classifies the move instead of listing random headlines
- separates primary and secondary drivers
- marks the weakly confirmed leg clearly

---

## Example 4 — weak-evidence case

```text
Market Sentinel.skill | Low-confidence scan

Task type
- market_sweep

Market tone
- market_tone: unresolved
- regime_classification: unclear
- action_state: observe
- escalation_needed: no

What is visible
- attention increased in a few names
- structural confirmation remains inconsistent
- event evidence is partial and may be stale

Working conclusion
- keep these names on watch, but do not treat them as high-conviction signals yet

Confidence
- confidence_level: low
- confirmation_status: weak
- missing_evidence: stronger cross-source confirmation
```

### Why this is a good output
- avoids certainty theater
- tells the user what is missing
- still gives a usable monitoring conclusion

---

## Example 5 — upstream handoff to a fuller trading agent

```text
Market Sentinel.skill | Upstream handoff

Task type
- holdings_review

Market tone
- market_tone: cautious
- regime_classification: macro_led
- action_state: handoff_now
- escalation_needed: yes

Priority holdings
1. BTC — review_priority: highest — risk_level: high — benchmark weakness is broadly confirmed
2. ETH — review_priority: high — risk_level: medium — derivatives pressure is rising

Watchlist rank
1. SOL — rank_bucket: high — confirmation_status: strong — leadership remains intact
2. DOGE — rank_bucket: attention_only — confirmation_status: weak — heat outruns structure

Downstream handoff
- what_to_do_next: re-check BTC and ETH risk controls first, then review SOL as the top external watchlist name
- what_not_to_assume: do not treat DOGE heat as execution-grade confirmation
- best_input_for_next_agent: holdings priority plus high-confirmation watchlist names
```

### Why this is a good output
- reads naturally to a human
- still exposes the fields another agent needs
- makes the downstream boundary explicit without pretending to be an execution engine
