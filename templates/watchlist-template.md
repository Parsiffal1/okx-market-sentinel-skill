# Watchlist Template

Use this when the user wants a ranked watchlist rather than a general summary.

## Rules
- ranking must be explainable
- separate confirmed names from noisy names
- if a symbol is hot but weakly confirmed, say so explicitly
- make the result easy to pass into a downstream trading agent

## Top-level context
- market_tone:
- regime_classification:
- escalation_needed:
- main_drivers:

## High priority
- Symbol:
- rank_bucket: high
- confirmation_status:
- Why now:
- Direct driver:
- What a downstream agent should review next:

## Medium priority
- Symbol:
- rank_bucket: medium
- confirmation_status:
- Why now:
- What would upgrade it:
- What a downstream agent should review next:

## Attention-only / unconfirmed
- Symbol:
- rank_bucket: attention_only
- confirmation_status:
- Why now:
- What is still missing:
- Why it is not ranked higher:
