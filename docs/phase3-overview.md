# Phase3 Overview

## 定位

Phase3 是整个项目唯一保留的主链路：

- 抓取多源真实数据
- 统一成状态视图
- 判断是否需要唤醒 Hermes
- 生成 OKX 可交易品种热度排名

它不再为任何已退役交易执行层服务。

## 主要脚本

- `scripts/phase3_pipeline.py`
  - 运行所有 source
  - 重建 cache / triggers
  - 写 markdown report
- `scripts/build_context_cache.py`
  - 聚合 holdings / macro / crypto_news / social / market
  - 输出 `market_state` / `holdings_state` / `hot_symbols_state`
- `scripts/build_triggers.py`
  - 输出 `llm_wake_triggers`
  - 输出 `observe_only_triggers`
  - 输出 `hot_symbols_ranking`
- `scripts/run_phase3_notifier.py`
  - 输出 Telegram 摘要与 markdown user report

## 关键状态块

- `market_state`：全市场风险/状态摘要
- `holdings_state`：持仓风险优先视图
- `hot_symbols_state`：上下文层热榜
- `wake_state`：是否需要 Hermes 介入

## 热度排名原则

`hot_symbols_ranking` 关注的是 **所有 OKX 合约可交易品种**，包括：

- crypto
- 美股相关合约
- 贵金属
- 大宗商品

排序会综合：

- 持仓优先
- 社媒热度
- CMC 补充
- OKX gainers
- OKX top OI
- OKX OI change
- OI × 价格四象限

## Trigger 哲学

Phase3 默认不叫醒 LLM。

只有当：

1. 宏观风险共振成立
2. 有真实持仓
3. 持仓已经在风险中

才会触发 `wake_hermes`。其余情况保持观察。
