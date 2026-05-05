# Phase 3 Semantic Event Model

## Design principle

Sources collect; the aggregator classifies.

No downstream semantic decision should depend only on source identity.

## Normalized event shape

Typical normalized event fields produced inside `build_context_cache.py`:

```json
{
  "fingerprint": "stable-id",
  "source": "jin10|blockbeats|okx_news|opennews",
  "source_type": "macro_summary|crypto_news|high_impact_events|...",
  "published_at": "ISO-8601|null",
  "title": "headline",
  "summary": "body/summary",
  "symbols": ["BTC", "ETH"],
  "event_domain": "primary semantic domain",
  "event_domains": ["ordered", "multi-label", "domains"],
  "event_subtype": "primary subtype",
  "event_subtypes": ["ordered", "subtypes"],
  "importance": "high|medium|low|unknown",
  "holds_match": true,
  "novelty": "new|seen",
  "event_score": 12.0
}
```

## Event domains

- `macro`
  - traditional macro releases and central-bank style events
- `geo`
  - geopolitics, sanctions, war/shipping risk, broad US-equity risk sentiment proxies
- `crypto_native`
  - crypto-internal headlines, whales, listings, upgrades, token-specific developments
- `security`
  - exploits, hacks, active/post-active incident handling, postmortems
- `flow`
  - exchange in/outflow, reserve change, premium/basis style market-structure signals
- `institutional`
  - ETF, treasury accumulation, crypto-related proxy-equity developments
- `regulation`
  - freezes, enforcement, lawsuits, compliance/regulatory actions
- `noise`
  - irrelevant or filtered-out items

## Multi-label behavior

Phase 3 now keeps both a **primary** semantic label and an ordered **multi-label** view.

- `event_domain` = the primary routing label used for backwards compatibility
- `event_domains` = ordered semantic domains matched from the same event text
- `event_subtype` = primary subtype aligned with `event_domain`
- `event_subtypes` = ordered subtype list aligned with `event_domains`

Example:
- `Nasdaq rallies as BlackRock spot BTC ETF records strong inflows`
  - primary domain: `geo`
  - secondary domain: `institutional`
- `Tether freezes USDT with law-enforcement support after bridge exploit`
  - primary domain: `security`
  - secondary domain: `regulation`

This allows one event to contribute to more than one downstream view without forcing a breaking change in legacy consumers.

## Downstream mapping

### `macro`
Compatibility view. Built from semantic macro/geo events.

### `macro_context`
Forward-looking semantic view.

Fields:
- `regime`

`regime` enum:
- `bullish`
- `neutral`
- `bearish`
- `unknown`
- `geo_risk`
- `event_window`
- `summary`
- `summary_buckets`
  - `geo`
  - `macro_financial`
  - `us_equity_sentiment`

### `crypto_news`
Built from semantic domains:
- `crypto_native`
- `flow`
- `institutional`
- `regulation`
- `security`

### `security`
Dedicated semantic lane:
- `events`
- each event keeps `state`
  - `live_exploit`
  - `post_exploit_active`
  - `postmortem`

### `signal_inputs`
Derived features for consumer migration.

Current fields:
- `holdings_related_new_events`
- `us_equity_risk_events`
- `security_events`

## Trigger consumption

`build_triggers.py` now consumes semantic evidence in addition to compatibility views.

Examples:
- semantic security event can wake Hermes even if legacy `security_events` summary is missing
- US-equity-risk proxy shift can produce observe-only trigger
- multiple new high-importance held-symbol events can produce event-cluster wake trigger

## Migration status

Completed:
- semantic event normalization
- semantic domain routing
- multi-label domain retention for cross-domain events
- security first-class lane
- macro summary dedupe/compression/bucketing
- semantic trigger inputs
- semantic notifier/report sections
- compatibility top-level semantic keys

Remaining future refinement:
- more granular subtypes
- domain-specific confidence / weighting for cross-domain events
- eventual legacy key removal after all consumers migrate
