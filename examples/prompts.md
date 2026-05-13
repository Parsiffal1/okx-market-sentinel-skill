# Example Prompts

This file is meant to make the skill easier to test, tune, and compare.

For each prompt below, a good answer should be:
- holdings-aware when holdings are present
- ranked rather than dumped
- explicit about drivers
- explicit about uncertainty
- short enough to be operationally useful

---

## Prompt Set A — Holdings-first

### Prompt A1
```text
Run a market sentinel pass. Review my holdings first, then tell me what else deserves attention.
Holdings: BTC, ETH, SOL.
Output style: short operator brief.
```

**A good answer should:**
- start with BTC / ETH / SOL before discussing unrelated names
- identify whether risk is macro-led, crypto-native, mixed, or unclear
- rank which holding deserves immediate review first
- then add a short watchlist beyond the current holdings

### Prompt A2
```text
Reassess these positions using current market, macro, and crypto-native information.
Holdings: XRP, DOGE, BTC.
Tell me which position is most fragile right now and why.
```

**A good answer should:**
- rank the three positions rather than treating them equally
- explain fragility using actual evidence categories
- avoid replacing structure confirmation with pure attention heat

---

## Prompt Set B — Full market sweep

### Prompt B1
```text
Scan the market and rank the symbols worth watching now.
Keep the answer under 12 bullets.
```

**A good answer should:**
- produce a shortlist, not a giant market dump
- explain why each symbol made the list
- separate high-confirmation names from heat-only names

### Prompt B2
```text
Give me a market sentinel summary for the current session, with the main drivers and a short watchlist.
```

**A good answer should:**
- include market tone
- identify the top drivers
- give a short watchlist with clear ranking logic
- explicitly say when evidence is mixed

---

## Prompt Set C — Event-driven follow-up

### Prompt C1
```text
Search for the strongest current macro and crypto-native drivers behind today's move and separate real risk from noise.
```

**A good answer should:**
- split evidence into macro vs crypto-native vs attention
- avoid treating every loud topic as equally important
- say which signal category is strongest

### Prompt C2
```text
Tell me whether this looks like a macro-led move, a crypto-native shock, or a mixed regime.
Explain the decision in plain language.
```

**A good answer should:**
- choose one of the defined regimes when possible
- justify the classification with evidence
- use `unclear` or `mixed` honestly when needed

---

## Prompt Set D — Brief formatting

### Prompt D1
```text
Turn the latest scan into a Telegram-style brief.
Keep it short, but do not lose the ranking or uncertainty notes.
```

**A good answer should:**
- keep the top conclusion
- keep holdings priority if relevant
- keep the ranked watchlist
- keep at least one explicit uncertainty line

### Prompt D2
```text
Give me a short operator note with evidence and uncertainty clearly marked.
```

**A good answer should:**
- read like an actual working note
- not sound like a generic market newsletter
- keep evidence and uncertainty visible without being verbose

---

## Prompt Set E — Upstream handoff

### Prompt E1
```text
Run a market sentinel pass and format the answer so a downstream trading agent can reuse it.
Keep the result short, but preserve holdings priority, main drivers, escalation, and missing evidence.
```

**A good answer should:**
- expose stable semantic fields rather than loose prose only
- make it obvious what should be reviewed next
- make it obvious what is still weakly confirmed
- avoid pretending it is already an execution instruction

### Prompt E2
```text
I already have a strategy agent. I only need the upstream market-intelligence layer.
Review BTC, ETH, and SOL first, then give me the top external watchlist names.
```

**A good answer should:**
- clearly separate current holdings from external watchlist names
- preserve ranking and driver attribution
- make the handoff usable for a downstream execution or risk module

---

## Prompt Set F — Failure tests

### Prompt F1
```text
These names are trending online. Tell me the top 5 to buy right now.
```

**A good answer should:**
- resist turning attention alone into conviction
- reframe the task into monitoring / risk interpretation
- distinguish social heat from structural confirmation

### Prompt F2
```text
I don't care about my current holdings. Just give me the hottest new names.
My current holdings are BTC, ETH, SOL.
```

**A good answer should:**
- still recognize that holdings are part of the risk picture
- explain that ignoring them entirely weakens the usefulness of the scan
- if the user insists, clearly separate `current exposure` from `new names`
