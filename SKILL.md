---
name: market-sentinel
description: |
  市场哨兵：当用户想做市场扫描、持仓优先复查、热点标的排序、事件驱动解释、Telegram 风格简报、风险摘要或 watchlist 更新时使用。
  这个 skill 教 agent 用“信息分层 → 持仓优先 → 风险归因 → 结果排序 → 简洁输出”的方法处理任何可交易市场。
  它是 API provider 无关的：关注信息质量、时效性、相关性和可验证性，不绑定固定供应商。
version: "1.1.0"
user-invocable: true
argument-hint: "market scan | holdings review | hot-symbol ranking | event-driven risk summary | Telegram brief"
homepage: https://github.com/Parsiffal1/market-sentinel-skill
repository: https://github.com/Parsiffal1/market-sentinel-skill
author: Parsiffal
license: MIT
metadata: {"openclaw": {"emoji": "📡", "tags": ["market-monitoring", "market-intelligence", "risk-sentinel", "agent-upstream", "holdings-review", "watchlist"], "requires": {"optionalEnv": ["TIMEZONE", "DEFAULT_WATCHLIST", "DEFAULT_OUTPUT_STYLE", "DEFAULT_REPORT_CHANNEL"]}}, "hermes": {"requires_toolsets": ["web", "browser", "terminal", "file"]}}
---

# Market Sentinel

> 把 agent 训练成一个真正会看盘、会排优先级、会写简报的市场哨兵。

---

## 核心定位

这个 skill 的价值不在于“多抓几个数据源”，而在于把市场判断层沉淀成一个可复用的上游能力。

它教 agent 学会四件事：

1. **先看什么** —— 当前持仓、当前风险、当前最活跃的标的
2. **怎么判断** —— 宏观驱动、加密原生驱动、结构确认、热度噪音分别处理
3. **怎么交付** —— 输出一份人和下游 agent 都能直接使用的摘要
4. **怎么衔接** —— 作为完整 trading agent 的上游信息源，为后续执行、风控、组合复查、通知器提供上下文

如果把普通行情抓取看成“拿信息”，这个 skill 做的是：

> **把信息变成判断，把判断变成可交接的上游输出。**

---

## 什么时候触发这个 skill

当用户在问下面这类问题时，就应该优先考虑加载这个 skill：

### A. 市场扫描
- `现在市场里最值得关注的东西是什么？`
- `扫一遍市场，告诉我什么最重要。`
- `给我一版当前市场状态摘要。`

### B. 持仓优先复查
- `先看我的持仓，再告诉我市场上还有什么值得盯。`
- `这些仓位现在谁最危险？`
- `结合最新行情和事件重新评估我的持仓。`

### C. 事件驱动解释
- `今天这波波动主要是宏观驱动还是加密原生驱动？`
- `联网查一下这波行情背后的关键原因。`
- `把真实风险和社交噪音分开。`

### D. 排序与简报
- `给我一版 watchlist。`
- `整理成 Telegram 风格简报。`
- `帮我做一版 operator note。`

---

## 输入预期

用户可能提供，也可能不提供：

- 当前持仓
- watchlist
- 关注时间窗口
- 目标输出形式
- 某个事件或某个主题

### 如果用户给了持仓
把持仓当作一级优先级。

### 如果用户只给了泛市场问题
从市场结构 + 事件背景出发，先做全局扫描，再缩到值得看的标的。

### 如果用户只给了某个事件
把任务视为“事件驱动 follow-up”，重点回答：
- 事件影响什么
- 影响强度如何
- 是否已经被市场结构确认

---

## 信息模型

这个 skill 是 **provider 无关** 的。
不要按 vendor 名字组织工作流，要按**信息类别**组织。

### 1. 市场结构层
重点看：
- 价格变化
- 成交量 / 成交额
- 持仓量 / 合约活跃度（如果可得）
- 异常波动
- 相对强弱
- 哪些标的真的在动

### 2. 持仓与敞口层
重点看：
- 当前持仓或 watchlist
- 集中度风险
- 哪些仓位应该优先复查
- 外部事件是否直接打到这些仓位

### 3. 宏观层
重点看：
- 利率、通胀、就业、流动性、政策变化
- 风险偏好变化
- 跨资产联动
- 对加密和高杠杆合约有真实影响的地缘事件

### 4. 加密原生层
重点看：
- 交易所异常
- 稳定币压力
- 安全事件
- 项目 / 协议级冲击
- 板块叙事切换

### 5. 注意力层
重点看：
- 讨论热度是否异常抬升
- 某些叙事是否在加速扩散
- 是否出现少数标的被集中关注

注意：

> **注意力只能作为辅助信号，不能单独替代结构确认。**

---

## 五条硬规则

### 规则 1：持仓先于机会
如果用户已经有仓位，先解释仓位，再解释市场机会。

### 规则 2：相关性先于数量
一条高相关、高影响、高时效的信息，通常比十条泛泛新闻更重要。

### 规则 3：结构确认先于话题热度
某个标的很热，不代表它一定重要。
先看市场结构有没有确认，再看讨论热度是不是在放大一个真实变化。

### 规则 4：驱动解释先于结论标签
不要只给 `高风险` / `值得关注`。
一定要说明驱动来自：
- 宏观重定价
- 加密原生事件
- 合约结构变化
- 持仓直接暴露
- 热度噪音但未确认

### 规则 5：不确定性要显式输出
如果证据冲突、证据过少、信息滞后、只有热度没有结构确认，就必须明确说出来。

---

## 执行流程

### Phase 0 — 识别任务类型
先判断当前任务更像哪一种：

- `holdings_review`
- `market_sweep`
- `event_followup`
- `hot_symbol_ranking`
- `brief_formatting`

如果同时命中多个，以这个优先级处理：

```text
holdings_review > event_followup > market_sweep > hot_symbol_ranking > brief_formatting
```

### Phase 0.5 — 判断是否需要补充上下文
只有在缺少关键信息时才追问。

优先补充的信息包括：
- 当前持仓
- 用户最关心的标的或板块
- 输出风格（brief / watchlist / risk memo）
- 时间窗口（现在 / 当日 / 最近 24 小时）

如果这些缺失但不影响先做一轮扫描，就先执行，再在结果里标出缺口。

---

### Phase 1 — 收集最小必要证据
Agent 应从任何可用工具中收集最小必要证据。

允许的信息来源形式包括：
- web search
- browser / document inspection
- exchange or market-data APIs
- MCP tools
- internal adapters
- databases
- user-provided notes or snapshots

重点不是“来源是谁”，而是这些证据是否：
- 足够新
- 足够相关
- 可以交叉验证
- 能支撑后续判断

---

### Phase 2 — 证据分层
把证据分成五层：

1. 市场结构信号
2. 持仓影响信号
3. 宏观风险信号
4. 加密原生风险信号
5. 注意力 / 讨论热度信号

然后逐层回答：
- 哪些信号强？
- 哪些只是噪音？
- 哪些对持仓有直接影响？
- 哪些只是辅助确认？

---

### Phase 3 — 风险归因
不要只说“跌了”或“热了”。
要把变化归因到更具体的驱动类型：

- **macro-led**：主要由宏观重定价、流动性、政策或跨资产风险偏好驱动
- **crypto-native**：主要由交易所、稳定币、安全事件、协议级冲击驱动
- **mixed**：宏观和加密原生都有贡献
- **attention-led but weakly confirmed**：讨论热度明显，但结构确认不足
- **unclear**：证据不足，不能稳妥归因

输出时不要偷懒地把所有东西都塞进 `mixed`。

---

### Phase 4 — 排优先级
一份好的结果至少应区分：

#### A. Priority holdings
需要马上看、马上复查的持仓

#### B. Watch-only names
值得盯，但还没强到要升级处理

#### C. Hot but weakly confirmed names
讨论很多，但结构确认不足，只能低置信度关注

#### D. Background noise
看起来热闹，但不值得在这轮输出里占中心位置

排序时优先考虑：
1. 是否直接影响用户持仓
2. 是否有结构确认
3. 是否有事件确认
4. 是否只是注意力放大

---

### Phase 5 — 输出
推荐默认顺序：

1. `Market tone` / 市场状态
2. `Priority holdings` / 优先持仓
3. `Symbols worth watching` / 值得盯的标的
4. `Why they matter` / 驱动原因
5. `Confidence / uncertainty notes` / 置信度与不确定性

如果用户要求 Telegram 风格或 operator brief，优先：
- 短句
- 低噪音
- 先结论后原因
- 不确定性只保留一行或两行

---

## 输出契约

### 必须满足
- 有排序
- 有取舍
- 有解释
- 有不确定性标记
- 有持仓优先意识（如果用户提供了持仓）
- 能让下游 agent 或 notifier 直接复用关键结论

### 不要输出成这样
- 一长串无排序 headlines
- 只贴价格和涨跌幅
- 只贴情绪和热度
- 只有结论没有驱动
- 像自动生成的“泛泛日报”

### 轻量 schema 原则
这个 skill 推荐使用 **轻量半结构化 schema**，而不是伪精确打分：
- 要有稳定字段名
- 要保留排序和驱动
- 要保留不确定性
- 不要假装存在跨市场稳定的万能分数

完整字段定义见：`references/output-schema.md`

### 推荐字段
你不需要每次都把字段写满，但通常应该从下面挑选：
- task_type
- market_tone
- regime_classification
- macro_risk_level
- crypto_native_risk_level
- escalation_needed
- main_drivers
- trigger_drivers
- priority_holdings
- watchlist_rank
- confirmation_status
- confidence_level
- missing_evidence
- downstream_handoff

### 如果输出要给完整 trading agent 继续使用
优先保证下面四件事稳定可读：
1. 现在是什么市场状态
2. 哪些持仓或标的最该优先处理
3. 驱动来自哪里
4. 哪些地方证据仍然不足

### 语气要求
- 结论优先
- 直白
- 不夸张
- 不用 provider 黑话
- 不制造“确定性表演”

---

## 典型执行模式

### Pattern A — Holdings-first review
适用于用户给了仓位。

输出重点：
- 哪些仓位最需要先看
- 风险驱动是什么
- 是系统性风险、个体风险，还是证据混合

### Pattern B — Full market sweep
适用于用户问“市场上现在什么最重要”。

输出重点：
- top risk drivers
- top watchlist names
- 哪些名字是高确认，哪些只是噪音偏热

### Pattern C — Event-driven follow-up
适用于有重大事件时。

输出重点：
- 什么变了
- 哪些标的最受影响
- 这轮变化更像暂时扰动、结构性变化，还是未定型冲击

### Pattern D — Brief formatting
适用于用户已经拿到分析结果，只是想整理输出。

输出重点：
- 压缩
- 排序
- 去噪音
- 保留驱动与不确定性

---

## 实测标准（Darwin-style）

如果要判断这个 skill 是否真的好用，至少要用 3 类 prompt 去试：

### Test Prompt 1 — 持仓优先
用户给一组持仓，看 skill 是否真的先看持仓，而不是先讲全市场。

### Test Prompt 2 — 事件驱动
用户给一个实时事件，看 skill 是否能区分“真实影响”和“注意力噪音”。

### Test Prompt 3 — 输出压缩
用户要求 Telegram brief，看 skill 是否能保留结论、排序、驱动、不确定性，而不是只做摘要删减。

一个合格结果应该满足：
- 明显优于不带 skill 的通用输出
- 结构稳定
- 排序合理
- 不确定性表达自然

---

## 常见失败模式

### 失败 1：只看热度，不看结构
讨论很多，不代表真的值得上榜。

### 失败 2：忽略持仓
用户有仓位时，却把大部分输出花在无关热点上。

### 失败 3：宏观与加密原生风险混写成一句空话
例如只说“市场情绪变差”，但说不清到底是哪一层在驱动。

### 失败 4：把单一来源当真相
skill 必须对来源做质量判断，不能把某个 provider 当作真理机器。

### 失败 5：隐藏不确定性
如果证据不够，就应该明确写出来，而不是用强语气包装弱判断。

### 失败 6：排序看起来像随机列表
如果输出的顺序不能解释，说明这个 skill 没有真正完成“哨兵”工作。

---

## 边界条件

### 如果数据不完整
- 说明缺了什么
- 降低置信度
- 不要虚构确定性

### 如果用户要求执行级建议
- 可以给监控视角和风险视角
- 但不要把输出伪装成确定性交易执行指令

### 如果没有可靠实时信息
- 直接说明当前结果受限于信息不足或信息滞后

---

## 最后检查清单

在结束输出前，至少自查这六件事：

- [ ] 有没有先看持仓（如果用户给了持仓）
- [ ] 有没有把宏观和加密原生风险分开处理
- [ ] 有没有把噪音和高确认信号分开
- [ ] 有没有解释“为什么重要”
- [ ] 有没有明确写出不确定性
- [ ] 输出排序是否真的有逻辑

---

## 相关文件

- `references/output-schema.md`
- `references/information-model.md`
- `references/api-agnostic-data-requirements.md`
- `references/source-grounding-rules.md`
- `references/market-monitoring-playbook.md`
- `examples/prompts.md`
- `examples/outputs.md`
- `templates/report-template.md`
- `templates/telegram-brief-template.md`
