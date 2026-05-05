# Portfolio Demo Walkthrough

## Demo 主线

这个项目现在最适合演示的是：

> 用真实多源数据，持续构建一个 OKX 可交易品种风险哨兵与热度排名系统。

## Step 1 — 跑主链路

```bash
python scripts/phase3_pipeline.py
```

展示：

- `context/context_cache.json`
- `context/trigger_candidates.json`
- `reports/phase3_report_*.md`

## Step 2 — 讲风险哨兵

重点解释：

- 为什么默认不唤醒 LLM
- 哪些条件下才会 `wake_hermes`
- 为什么强调 holdings-aware 风险门控

## Step 3 — 讲热度排名

重点解释：

- 热榜覆盖所有 OKX 合约可交易品种
- 不只看 CMC，还看 OKX gainers / OI / OI change
- OI × 价格四象限如何提供更交易所原生的异动视角

## Step 4 — 展示通知

```bash
python scripts/run_phase3_notifier.py
```

展示内容：

- Trigger 判定
- 热度排名
- API Health
- 宏观 / 地缘变化
- 重点新闻

## 面试/展示表达

可以把它描述为：

- 一个 artifact-first 的市场状态层
- 一个非 LLM 默认驱动的风险哨兵
- 一个面向 OKX 可交易品种的热度监控上游
