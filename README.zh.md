[English](README.md) | [中文](README.zh.md)

<div align="center">

# 市场哨兵 Skill

> *把 agent 训练成真正会看盘的操作员。*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Compatible-blueviolet)](https://skills.sh)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

<br>

**一个服务交易者的市场监控与判断 skill。**

它帮助交易者联网搜索实时市场证据、先看持仓、区分宏观风险和加密原生风险、判断一个变化应该继续观察还是更严肃地处理，并把这些内容整理成一份真正能用的工作简报。

如果需要，它也可以继续被 agent workflow 或 trading system 复用。

[效果示例](#效果示例) · [安装](#安装) · [你能得到什么](#你能得到什么) · [触发逻辑](#触发逻辑) · [工作方式](#工作方式) · [也适合-trading-agent-复用](#也适合-trading-agent-复用) · [接下来先看什么](#接下来先看什么)

```bash
npx skills add Parsiffal1/market-sentinel-skill
```

</div>

---

## 效果示例

```text
市场哨兵｜扫描完成

市场状态
- market_tone: cautious
- regime_classification: macro_led
- macro_risk_level: high
- crypto_native_risk_level: medium
- action_state: escalate
- escalation_needed: yes

主要驱动
- macro repricing
- cross-asset weakness
- derivatives pressure in majors

优先持仓
1. BTC —— review_priority: highest —— risk_level: high —— 基准资产走弱已被确认
2. ETH —— review_priority: high —— risk_level: medium —— 衍生品活跃度正在上升

观察名单
1. SOL —— confirmation_status: strong —— 结构确认和注意力抬升同时出现
2. DOGE —— confirmation_status: weak —— 热度是真实的，但确认仍不完整

置信度
- confidence_level: medium
- missing_evidence: 次级叙事还需要更强确认
```

这就是这个 skill 的核心价值：
**不是多给你几条新闻，而是把判断层交付出来。**

---

## 这个项目是什么

市场哨兵是一个面向交易者和操作员的公开 skill 仓库，目标是帮助人更好地监控实时市场并得出可用结论。

它首先是一个服务交易者本身的 skill。
如果有人希望把同样的判断层复用进更大的 trading stack，它也可以兼容 agent workflow。
它不绑定某个固定交易所、券商、新闻源、社交源或 MCP 服务。
它真正关心的是：agent 能不能拿到足够**相关、及时、可交叉验证**的信息，去回答这些问题：

- 我当前持仓里，谁最该先看？
- 这轮行情更像宏观主导、加密原生主导、混合，还是仍然不清楚？
- 现在哪些标的值得盯？
- 下游 trading agent、通知器或研究流程下一步应该重点看什么？

---

## 你能得到什么

### 1. 持仓优先的市场复查
只要当前有持仓，skill 就先从当前敞口开始，而不是先追逐新热点。

### 2. 排过序的观察名单
不是简单的涨跌榜。
而是一份带原因、带确认质量、带升级条件的短名单。

### 3. 驱动归因
这个 skill 会明确区分：
- 宏观压力
- 加密原生压力
- 混合状态
- 注意力主导但确认弱
- 尚不清楚

### 4. 需要时可复用的交接结果
它的输出足够结构化，可以直接喂给：
- 另一位交易者
- 研究流程
- Telegram notifier
- dashboard 或 memory layer
- 如果你需要，也可以接给下游 trading agent

---

## 也适合 trading agent 复用

如果你在做**完整 trading agent**，这个 skill 也可以作为其中的市场判断层被复用。

在那种 setup 里，市场哨兵主要负责回答：
- 现在什么最重要
- 什么需要升级关注
- 哪些持仓暴露最高
- 哪些观察名单已经被结构确认
- 还缺哪些证据

大多数 stack 已经会抓数据。
真正稀缺的是：能不能判断一个名字现在只是继续观察、需要升级复查，还是应该立刻交给更完整的风险或执行流程。

```text
live sources -> Market Sentinel -> downstream trading agent -> execution / risk / monitoring subsystems
```

在这条链路里，市场哨兵提供的是**判断与排优先级**。
下游 agent 再决定如何：
- 调整组合复查优先级
- 收紧风控约束
- 触发更深的策略模块
- 通知人工操作员
- 只把高优先级上下文送进执行逻辑

如果你想看这种交接方式的稳定字段，直接读 [`references/output-schema.md`](references/output-schema.md)。

---

## 触发逻辑

市场哨兵不只要回答*什么重要*。
它还应该在监控层上回答：下游系统下一步应该怎么处理。

推荐三种 action state：
- `observe` —— 值得继续观察，但还不够强，不必立刻进入更深下游流程
- `escalate` —— 值得交给下游 agent、风险模块或人工操作员做进一步复查
- `handoff_now` —— 应该立即转入更完整的 trading / risk workflow

一个简单经验是：
- 持仓受到直接且已确认的压力时，默认偏向 `escalate`
- 多层信号同向时，可以支持 `escalate` 或 `handoff_now`
- 只有热度没有结构确认时，通常应停留在 `observe`

完整触发契约见 [`references/trigger-policy.md`](references/trigger-policy.md)。

---

## 工作方式

### Step 1 — 先定义任务
一次好的扫描，先要判断用户要的是：
- 持仓复查
- 全市场扫描
- 事件 follow-up
- 热点标的排序
- 简报整理

### Step 2 — 收集实时证据
这个 skill 是 provider 无关的。
它不把工作流写死在某个 vendor 上。
它可以配合任何组合使用：
- web search
- browser / 文档阅读
- 行情接口或 API
- 持仓 / 账户状态输入
- 研究数据库
- MCP 工具
- 用户提供的上下文

### Step 3 — 按信息类别分层
市场哨兵要求 agent 用五层来思考：
- 市场结构
- 持仓与敞口
- 宏观背景
- 加密原生背景
- 注意力信号

### Step 4 — 对重要性排序
agent 需要分清：
- 哪些仓位要立刻复查
- 哪些名字值得盯
- 哪些名字虽然热但确认弱
- 哪些只是背景噪音

### Step 5 — 交付一个干净结果
最终结果要保留：
- 排序
- 驱动
- 不确定性
- 可以继续交给下游 agent 的紧凑摘要

更完整的执行说明见 [`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md)。

---

## 输出契约

市场哨兵刻意采用的是**轻量语义 schema**，而不是看起来很精密、实际上无法稳定解释的伪分数。

推荐的顶层字段包括：
- `task_type`
- `market_tone`
- `regime_classification`
- `macro_risk_level`
- `crypto_native_risk_level`
- `action_state`
- `escalation_needed`
- `main_drivers`
- `trigger_drivers`
- `priority_holdings`
- `watchlist_rank`
- `confirmation_status`
- `confidence_level`
- `missing_evidence`
- `downstream_handoff`

完整定义见 [`references/output-schema.md`](references/output-schema.md)。
触发与升级规则见 [`references/trigger-policy.md`](references/trigger-policy.md)。

---

## 安装

```bash
npx skills add Parsiffal1/market-sentinel-skill
```

如果你的 runtime 更喜欢本地 skill 目录，也可以直接把仓库放进去。

### 运行前提

这个 skill 默认假设 agent 至少具备以下一部分能力：
- web 访问
- browser 或文档阅读
- 行情接口
- 持仓或组合上下文
- 返回 brief / report / handoff 的能力

它不要求单一 provider 栈。

---

## 仓库结构

```text
README.md
README.zh.md
SKILL.md
references/
examples/
templates/
```

- `SKILL.md` —— 主运行契约
- `references/` —— 信息模型、grounding 规则、playbook、output schema
- `examples/` —— prompts、outputs、use cases
- `templates/` —— report、brief、watchlist 模板

---

## 接下来先看什么

- [`SKILL.md`](SKILL.md)
- [`references/output-schema.md`](references/output-schema.md)
- [`references/trigger-policy.md`](references/trigger-policy.md)
- [`references/information-model.md`](references/information-model.md)
- [`references/api-agnostic-data-requirements.md`](references/api-agnostic-data-requirements.md)
- [`references/source-grounding-rules.md`](references/source-grounding-rules.md)
- [`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md)
- [`examples/outputs.md`](examples/outputs.md)

---

## 边界

市场哨兵负责的是上游监控与判断层。
它帮助回答什么值得关注、为什么重要、什么应该升级处理。

更完整的 trading agent 仍然应该自己负责：
- 执行策略
- 仓位 sizing
- 止损 / 止盈逻辑
- venue-specific safety checks
- 账户权限与风控策略

如果接入真实交易所访问，信息层优先使用只读凭证。

---

## 许可证

[MIT](LICENSE)
