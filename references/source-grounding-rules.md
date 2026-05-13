# Source Grounding Rules

## Purpose
The skill should produce grounded monitoring output, not decorative summaries.

## Core rules

### 1. Evidence before conclusion
Do not make a strong claim unless the evidence category exists.

### 2. Current over familiar
A familiar source is not automatically better than a current source.

### 3. Specific over generic
`security incident affected withdrawals for exchange-linked assets` is stronger than `people are worried online`.

### 4. Cross-check when possible
If a move appears important, try to confirm it through at least two information categories:
- market structure + event
- holdings impact + event
- event + attention confirmation

### 5. Say when evidence is weak
Use phrases like:
- `evidence mixed`
- `confirmation partial`
- `attention elevated but structural confirmation weak`
- `insufficient evidence for a stronger claim`

## Citation style guidance
If the runtime supports citations, prefer citing:
- direct market data observations
- event descriptions
- user-provided holdings context
- current web evidence

If the runtime does not support formal citations, still describe where the conclusion came from:
- market structure
- macro events
- crypto-native events
- holdings exposure
- discussion heat
