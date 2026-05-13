[English](README.md) | [中文](README.zh.md)

<div align="center">

# 市场哨兵 Skill

**把 agent 训练成一个真正会看盘的操作员：会联网搜信息，会先看持仓，会区分真实风险和市场噪音，会写出人能直接使用的简报。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Compatible-blueviolet)](https://skills.sh)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

</div>

---

## 为什么要做这个 skill

很多市场监控流程都停得太早。

它们会抓价格，会拉新闻，会列涨跌榜。
但真正关键的那一步，往往没有被做好：

- *我现在的持仓里，谁最该先看？*
- *今天这波变化到底是宏观驱动、加密原生驱动，还是大部分只是噪音？*
- *在所有可交易标的里，哪些名字现在真的值得盯？*
- *怎么把这些信息整理成另一位操作员或 agent 能几秒读懂的简报？*

**市场哨兵做的，就是把这层判断能力沉淀成一个可复用 skill。**

它让 agent 能稳定地做到：
- 收集实时市场证据
- 按信息类型组织证据
- 优先处理当前敞口
- 对真正重要的对象排序
- 输出一份简洁、可解释、可继续行动的结果

---

## 你能得到什么

这个 skill 训练 agent 产出四类真正有用的结果。

### 1. 市场状态摘要
不只是“涨了跌了什么”，而是判断当前更像：
- 谨慎
- 混合
- 风险偏好上升
- 风险偏好下降
- 信号冲突、尚未定型

### 2. 持仓优先复查
如果用户已经有持仓，skill 应该先回答：
- 哪些仓位最该先看
- 哪些只是需要观察
- 哪些看起来很吓人，但证据还不够强

### 3. 热点标的短名单
对当前值得关注的标的做排序，并说明原因。

### 4. 可直接转发的操作员简报
最终输出应该像一份工作笔记，而不是一堆原始信息转储。

---

## Agent 应该关注哪些信息

这个仓库是刻意 **API provider 无关** 的。
它不按 vendor 名字定义工作流，而是按**信息类别**定义。

### 市场结构信息
- 价格变化
- 成交量 / 成交额
- 持仓量 / 合约活跃度（如果可得）
- 异常波动
- 相对强弱
- 哪些标的真的在活跃

### 持仓与敞口信息
- 当前持仓或 watchlist
- 集中度风险
- 与事件直接相关的仓位
- 哪些名字现在应该优先复查

### 宏观信息
- 利率、通胀、就业、流动性、政策变化
- 跨资产风险偏好
- 对加密和杠杆合约有真实影响的地缘事件

### 加密原生信息
- 交易所异常
- 稳定币压力
- 安全事件
- 项目 / 协议级冲击
- 板块叙事轮动

### 注意力与讨论热度
- 异常讨论热度
- 叙事扩散速度
- 少数标的是否被集中关注

这些信息可以来自：
- web search
- browser / 网页阅读
- 行情接口
- 内部系统
- 数据库
- MCP 工具
- 用户提供的上下文

---

## 核心循环

这个 skill 最适合 agent 按下面这个循环来执行：

### Step 1 — 先确定范围
用户到底要什么？
- 持仓复查
- 全市场扫一遍
- 某个事件后的 follow-up
- watchlist 更新
- 格式化简报

### Step 2 — 抓实时证据
从相关信息类别里拿到最少但足够的实时证据。

### Step 3 — 证据分层
把证据拆成：
- 市场结构
- 持仓影响
- 宏观驱动
- 加密原生驱动
- 注意力 / 讨论热度

### Step 4 — 排序
不是所有信号都值得同等重视。
skill 要帮助 agent 判断：
- 什么是真的急
- 什么值得盯
- 什么只是很吵但还没被确认

### Step 5 — 写简报
先给结论。
再给原因。
最后标不确定性。

更完整的执行方式见：[`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md)

---

## 典型 prompts

### 持仓优先
- `跑一轮市场哨兵，先复查我的持仓，再告诉我还有什么值得关注。`
- `结合当前市场、宏观和加密原生信息，重新评估这些仓位。`

### 全市场扫描
- `扫一遍市场，排出现在最值得看的名字。`
- `给我一版简洁的市场哨兵会话摘要。`

### 事件驱动 follow-up
- `联网搜索今天这波行情背后的主要驱动，把真正风险和噪音分开。`
- `告诉我这轮变化更像宏观主导、加密原生主导，还是混合状态。`

### 输出整理
- `整理成 Telegram 风格简报。`
- `给我一版带证据和不确定性说明的操作员短报告。`

更多示例见：[`examples/prompts.md`](examples/prompts.md)

---

## 示例输出

```text
市场哨兵｜扫描完成

市场状态
- 偏向：谨慎
- 是否需要升级关注：是
- 主驱动：宏观重定价 + 加密原生压力

优先持仓
1. BTC —— 跨资产走弱与事件聚集同时出现，风险抬升
2. ETH —— 衍生品活跃度上升，但板块情绪仍偏混合

值得盯的标的
1. SOL —— 结构确认较强，同时热度上升
2. DOGE —— 关注度冲高，但确认弱于 SOL

置信度说明
- 市场结构确认：高
- 事件确认：中
- 仅注意力信号质量：低到中
```

更多样例见：[`examples/outputs.md`](examples/outputs.md)

---

## 这个 skill 应该怎么思考

### 持仓先于新机会
如果用户已经有敞口，先回答这些敞口的问题，而不是先追新故事。

### 相关性先于信息量
一条精确、高影响的信息，通常比十条模糊新闻更值钱。

### 信息质量先于来源品牌
熟悉的 provider 不天然比一个实时、具体、可交叉验证的来源更可靠。

### 解释先于标签
不要只说 `高风险` 或 `值得关注`。
要说清楚是什么在驱动这个结论。

### 诚实先于确定性表演
如果证据混合，就明确说混合。
如果证据弱，就明确说弱。

---

## 推荐输出结构

一份好的默认答案通常长这样：

1. **市场状态**
2. **优先持仓**
3. **值得关注的标的**
4. **为什么重要**
5. **置信度 / 不确定性说明**

可直接复用的模板在：
- [`templates/report-template.md`](templates/report-template.md)
- [`templates/telegram-brief-template.md`](templates/telegram-brief-template.md)
- [`templates/watchlist-template.md`](templates/watchlist-template.md)

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

- `SKILL.md` 是主运行契约
- `references/` 解释信息模型和 grounding 规则
- `examples/` 给出 prompts、输出和使用场景
- `templates/` 提供可复用输出格式

---

## 安装与使用

### 安装成 skill

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

或者按你的 agent runtime 习惯，把仓库放进本地 skill 目录。

### 运行前提

这个 skill 默认假设 agent 具备以下一部分能力：
- web search
- browser / 文档阅读
- market-data tools or APIs
- holdings / account-state inputs
- messaging or reporting tools

它不依赖单一 provider 栈。

---

## 边界

这个 skill 负责的是：监控、整合、解释、输出。

它帮助回答：
- 现在什么最值得关注
- 哪些仓位应该先看
- 哪些信号是真的，哪些更像噪音

它不替代：
- 执行权限控制
- 风控政策
- 人的最终判断

如果接入真实交易所数据，优先使用**只读凭证**。

---

## 建议接下来先看

- [`SKILL.md`](SKILL.md)
- [`references/information-model.md`](references/information-model.md)
- [`references/api-agnostic-data-requirements.md`](references/api-agnostic-data-requirements.md)
- [`references/source-grounding-rules.md`](references/source-grounding-rules.md)
- [`examples/outputs.md`](examples/outputs.md)
