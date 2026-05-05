# Phase3 Handoff

## 下游该消费什么

现在下游只应该消费两类输出：

1. `wake_state` / `llm_wake_triggers` / `observe_only_triggers`
2. `hot_symbols_ranking`

不再存在任何旧执行层专用消费视图。

## 推荐读取顺序

1. `context/context_cache.json`
   - 看 `market_state`
   - 看 `holdings_state`
   - 看 `hot_symbols_state`
2. `context/trigger_candidates.json`
   - 看 `wake_state`
   - 看 `llm_wake_triggers`
   - 看 `observe_only_triggers`
   - 看 `hot_symbols_ranking`

## 热度排名使用建议

`hot_symbols_ranking` 适合给：

- 人工复盘
- 下游研究模块
- 定时播报
- 后续外部分析器

其含义是“当前值得优先关注的 OKX 可交易品种”，不是自动下单指令。

## 排名优先级

推荐理解顺序：

1. 已有持仓
2. OKX 原生异动（OI / 涨幅 / 四象限）
3. 白名单社媒热度
4. CMC 补充信号

## 通知侧应展示

- 持仓
- 风险等级
- 是否唤醒 LLM
- 观察级触发
- 热度排名
- 宏观 / 地缘变化
- 重点新闻
