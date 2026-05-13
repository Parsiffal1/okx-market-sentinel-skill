# Information Model

This skill uses a simple information model so an agent can stay provider-agnostic while still being concrete.

## 1. Market structure layer
Questions:
- What is moving?
- How unusual is the move?
- Is the move broad or concentrated?
- Is contract activity confirming the move?

Typical fields:
- symbol
- price change
- turnover / volume
- open interest or contract activity if available
- volatility note
- relative-strength note

## 2. Holdings layer
Questions:
- Which current positions deserve immediate attention?
- Which positions are being hit by the same driver?
- Is the user’s risk concentrated in one theme?

Typical fields:
- held symbol
- exposure priority
- direct risk driver
- urgency level

## 3. Macro layer
Questions:
- Is there a broad risk-on or risk-off backdrop?
- Is the move tied to policy, liquidity, or cross-asset repricing?

Typical fields:
- event class
- timing
- relevance to crypto / leveraged contracts
- confidence

## 4. Crypto-native layer
Questions:
- Is there exchange, stablecoin, protocol, or security stress?
- Is the issue isolated or systemic?

Typical fields:
- event class
- affected symbols or sectors
- potential spillover
- confidence

## 5. Attention layer
Questions:
- Which names are suddenly getting discussed more?
- Is the attention confirmed by market structure or just narrative noise?

Typical fields:
- heat change
- narrative label
- confirmation status

## 6. Output layer
A good final answer should combine the layers into:
- market summary
- holdings review
- hot-symbol ranking
- confidence notes
