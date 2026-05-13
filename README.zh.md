[English](README.md) | [中文](README.zh.md)

<div align="center">

# OKX 市场哨兵 Skill

**一个 OKX-first、API 提供商无关的市场监控 skill，用于让 agent 联网搜集信息、识别风险、筛选重点标的，并输出可执行摘要。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Compatible-blueviolet)](https://skills.sh)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-green)](https://skills.sh)

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

</div>

---

## 这是什么

OKX 市场哨兵是一个**市场监控 skill**，不是交易机器人，也不是 dashboard 项目。

它的工作只有一件事：

> 帮 agent 把分散的市场信息整理成一个**持仓优先、可解释、可输出**的风险视图和观察清单。

它适合这样的任务：

- 先看当前持仓有没有需要立刻关注的风险
- 在 OKX 可交易标的里筛出现在值得看的名字
- 区分宏观风险和加密原生风险
- 把多源信息压缩成一份适合 operator / Telegram / 下游 agent 使用的简报

这个仓库现在是**彻底 skill-first** 的形态，不再附带沉重的参考实现、dashboard、测试工程或固定 provider 依赖。

---

## 这不是什么

这个 skill **不是**：

- 自动交易系统
- 下单程序
- 收益承诺工具
- 某几个固定 API 的包装壳
- 必须绑定某个资讯商或数据商才能工作的项目

只要 agent 能获得：
- 市场数据
- 当前事件信息
- 持仓/观察列表
- 联网搜索能力

这个 skill 就能工作。

---

## 核心价值

很多市场监控方案会失败，通常是因为两类问题：

1. **太原始**：只有价格、新闻、热度，没有真正的操作判断
2. **太狭窄**：只依赖一个来源、一个视角、一个信号

OKX 市场哨兵的作用，是给 agent 一套稳定的方法：

1. 收集市场结构信息
2. 收集宏观与加密原生事件
3. 先检查当前持仓
4. 对真正重要的对象排序
5. 输出一份简洁、可解释、可继续行动的结果

重要的是：

> **这个 skill 关注的是信息，不是信息供应商。**

---

## Agent 需要关注哪些信息

这个 skill 关心的是**信息类别**，而不是 vendor 名单。

### 1. 市场结构信息
- 价格变化
- 成交量 / 成交额
- 持仓量 / 合约活跃度（如果能拿到）
- 异常波动
- 相对强弱
- OKX 可交易标的中的热度变化

### 2. 持仓与敞口信息
- 当前持仓
- 集中度
- 哪些仓位应该优先复查
- 哪些事件与当前持仓直接相关

### 3. 宏观信息
- 利率、通胀、就业、流动性、政策变化
- 跨资产风险偏好
- 可能影响加密和高杠杆合约的地缘冲击

### 4. 加密原生信息
- 交易所异常
- 稳定币压力
- 安全事件
- 项目级风险
- 板块叙事切换

### 5. 社交与注意力信息
- 讨论热度
- 某标的是否突然被集中关注
- 叙事扩散速度

这些信息可以来自：
- 网页搜索
- 行情接口
- 新闻检索
- 内部工具
- 数据库
- MCP 服务
- 用户提供的上下文

skill 不要求固定供应商。

---

## 这个 skill 应该输出什么

一个好的执行结果，通常应该包含这些部分：

### A. 风险摘要
- 当前市场偏向什么状态
- 和上一轮相比，什么变了
- 风险是在上升、持平，还是混合

### B. 持仓优先复查
- 哪些当前持仓最该先看
- 驱动风险的核心因素是什么
- 这是系统性风险、个体风险，还是证据不足的风险

### C. 热点标的清单
- 当前最值得关注的 OKX 可交易标的
- 它们为什么上榜
- 哪些信号支持这个排序

### D. 简报输出
例如：

```text
OKX 市场哨兵｜扫描完成

市场状态
- 偏向：谨慎
- 是否需要升级关注：是
- 主驱动：宏观事件窗口 + 加密原生压力

优先持仓
1. BTC —— 跨资产走弱 + 事件聚集，风险抬升
2. ETH —— 衍生品压力与板块外溢需要继续观察

值得盯的标的
1. SOL —— 热度上升 + 合约活跃度增强
2. DOGE —— 关注度冲高，但结构确认不足

置信度说明
- 宏观信号强度：高
- 加密原生事件确认：中
- 社交信号可靠性：偏混合
```

---

## 典型使用方式

### 通用扫描
- `跑一轮 OKX 市场哨兵，给我一个简洁风险摘要。`
- `看一下 OKX 可交易合约里现在最值得关注的标的。`

### 持仓优先扫描
- `先重查我当前持仓，再告诉我还有哪些值得盯。`
- `结合我的持仓，告诉我哪些仓位现在最需要注意，以及原因。`

### 事件驱动扫描
- `结合最新宏观和加密原生事件，判断现在是不是风险偏高窗口。`
- `联网搜索今天主要驱动因素，把噪音和真正风险分开。`

### 输出整理
- `把这轮扫描整理成 Telegram 风格简报。`
- `给我一版带证据和不确定性说明的 watchlist。`

更多示例见：[`examples/prompts.md`](examples/prompts.md)

---

## 这个 skill 应该如何思考

### 原则 1：先持仓，后新机会
如果用户已经有持仓，先看持仓，而不是先找新故事。

### 原则 2：信息比来源品牌更重要
skill 不应该因为某条信息来自某个 provider 就自动抬高权重。真正重要的是：时效性、明确性、可交叉验证性。

### 原则 3：热度不等于风险重要性
很热的话题，可能只是噪音；一个讨论不多但影响极大的运营事件，可能更重要。

### 原则 4：要解释驱动，不要只贴标签
不要只说 `风险高`。要说清楚：是宏观重定价、交易所压力、持仓量变化、安全事件，还是证据不充分的注意力信号。

### 原则 5：诚实表达不确定性
如果证据冲突、来源滞后、信息不足，输出必须明确标出来。

---

## Skill 工作流

一个高质量执行通常应该是：

1. 明确范围
   - 持仓？watchlist？全市场？单一板块？
2. 收集市场结构信息
3. 收集宏观与加密原生事件
4. 如有必要，补充社交与注意力信息
5. 比较不同类别信号的质量
6. 只保留真正值得提醒的对象
7. 输出一份有证据、有排序、有不确定性说明的结果

更详细版本见：[`references/market-monitoring-playbook.md`](references/market-monitoring-playbook.md)

---

## 关于来源与联网搜索

这个 skill 明确支持 agent：

- 联网搜索
- 读取网页
- 调用市场数据接口
- 读取账户/持仓信息
- 从任意可用信息源提取证据

但它要求 agent 遵守这些规则：

- 优先使用**当前信息**，不要拿旧总结冒充实时判断
- 优先使用**直接相关证据**，不要用泛泛评论替代事实
- 尽量做**交叉验证**，不要过度依赖单一来源
- 不要把来源品牌当成结论本身

更详细规则见：[`references/source-grounding-rules.md`](references/source-grounding-rules.md)

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
- `references/` 解释信息模型与判断规则
- `examples/` 给出 prompt、输出和使用场景
- `templates/` 提供可复用输出模板

---

## 安装与使用

### 安装 skill

```bash
npx skills add Parsiffal1/okx-market-sentinel-skill
```

或者按你使用的 agent runtime，把仓库复制到本地 skill 目录。

### 运行前提

这个 skill 默认假设 agent 具备以下某些能力：

- web search
- browser / document reading
- market-data tools or APIs
- holdings / account state inputs
- messaging or reporting output tools

它**不依赖单一 provider 栈**。

---

## 安全边界

这个 skill 只负责监控与解释。

它不替代：
- 人工判断
- 执行权限控制
- 真正的风控策略

如果接入真实交易所数据，请优先使用**只读凭证**。
不要把 skill 输出当成收益承诺或个性化投资建议。

---

## 建议接下来先看

- [`SKILL.md`](SKILL.md)
- [`references/information-model.md`](references/information-model.md)
- [`references/api-agnostic-data-requirements.md`](references/api-agnostic-data-requirements.md)
- [`examples/outputs.md`](examples/outputs.md)
