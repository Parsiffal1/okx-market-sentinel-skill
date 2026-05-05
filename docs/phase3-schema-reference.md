# Phase3 Schema Reference

## `context/context_cache.json`

关键字段：

- `macro`
- `crypto_news`
- `social`
- `holdings`
- `market_state`
- `holdings_state`
- `hot_symbols_state`
- `signal_inputs`
- `health`

## `context/trigger_candidates.json`

关键字段：

- `generated_at`
- `schema_version`
- `llm_wake_required`
- `llm_wake_triggers`
- `observe_only_triggers`
- `hot_symbols_ranking`
- `wake_state`

## `hot_symbols_ranking[*]`

每一项通常包含：

- `symbol`
- `source`
- `priority`
- `reasons`

说明：

- `source` 表示主要来源或组合来源
- `priority` 是排序等级，不是交易动作
- `reasons` 用于解释为什么它进入榜单

## 常见 reason

- `existing_holding`
- `high_social_heat`
- `multi_account_discussion`
- `cmc_trending_symbol`
- `okx_top_gainer_24h`
- `okx_top_oi_contract`
- `okx_oi_change_leader`
- `okx_oi_price_up_quadrant`
- `okx_oi_short_build_quadrant`
- `okx_oi_short_cover_quadrant`
- `okx_oi_long_exit_quadrant`

## `wake_state`

字段：

- `llm_wake_required`
- `wake_priority`
- `wake_reasons`
- `observe_only_reasons`
