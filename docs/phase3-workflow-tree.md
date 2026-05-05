# Phase3 Workflow Tree

```text
phase3_pipeline.py
├─ run source fetchers
│  ├─ okx_market
│  ├─ okx_positions
│  ├─ blockbeats
│  ├─ cmc
│  ├─ moss_xsignal
│  ├─ okx_news
│  ├─ opennews
│  ├─ opentwitter
│  └─ jin10
├─ build_context_cache.py
│  ├─ normalize multi-source state
│  ├─ build market_state
│  ├─ build holdings_state
│  ├─ build hot_symbols_state
│  └─ write context/context_cache.json
├─ build_triggers.py
│  ├─ build llm_wake_triggers
│  ├─ build observe_only_triggers
│  ├─ build hot_symbols_ranking
│  │  ├─ holdings first
│  │  ├─ OKX market moves
│  │  ├─ whitelist social heat
│  │  └─ CMC supplement
│  └─ write context/trigger_candidates.json
└─ run_phase3_notifier.py
   ├─ render trigger diagnostics
   ├─ render 热度排名
   ├─ render API health
   ├─ render 宏观 / 地缘变化
   └─ send Telegram summary
```

## 设计原则

- 默认不唤醒 LLM
- 持仓优先
- 风险判断先于热榜解释
- 热榜是监控/研究输入，不是执行命令
