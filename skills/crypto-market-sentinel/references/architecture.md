# Architecture Overview

Crypto Market Sentinel is best understood as a **skill + runnable reference implementation**.

## Layers

### 1. Source fetchers
Located in `scripts/sources/`.

Examples:
- `okx_market_fetch.py`
- `okx_positions_fetch.py`
- `jin10_fetch.py`
- `okx_news_fetch.py`
- `blockbeats_fetch.py`
- `opennews_fetch.py`
- `opentwitter_fetch.py`

Responsibilities:
- talk to upstream sources
- normalize source-local payloads enough to cache them
- emit structured success / failure payloads

### 2. Context aggregation
Located in `scripts/build_context_cache.py`.

Responsibilities:
- aggregate source outputs
- derive market / holdings / news / macro state
- build normalized context artifacts
- compute risk state and related explanations

### 3. Trigger generation
Located in `scripts/build_triggers.py`.

Responsibilities:
- transform context into wake / observe / hot-symbol triggers
- keep decision logic separated from raw source fetchers

### 4. Delivery surfaces
- Dashboard: `dashboard/`
- Telegram notifier: `scripts/run_phase3_notifier.py`
- Reports: generated at runtime by the pipeline

### 5. Semantic Compass
- `config/semantic_compass.json`
- `scripts/semantic_compass.py`
- `scripts/refresh_semantic_compass.py`

Responsibilities:
- maintain the agent-refreshable phrase pack
- refine `geo_risk` and `news_risk` matching semantics
- bridge natural-language refresh briefs into concrete rule lists

## Key principle

Do not collapse all logic into one place.

The source layer, aggregation layer, trigger layer, and delivery layer are intentionally separated. When debugging or extending the project, first identify which layer owns the behavior.
