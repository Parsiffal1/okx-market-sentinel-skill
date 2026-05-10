[English](README.md) | [中文](README.zh.md)

# OKX 市场哨兵 Skill

一个面向 **OKX 优先市场监控与风险哨兵** 的项目型 skill 仓库：既包含可复用的 agent skill 包，也包含可直接运行的 Python 参考实现。

## 项目简介

OKX 市场哨兵要解决的，不是“再抓一个行情接口”，而是把**分散的市场、持仓、新闻、社媒和语义风险信号，整理成一个操作者和 agent 都能快速理解的监控结果**。

它适合那些已经不满足于单点抓数脚本、但又不想直接跳到自动交易系统的使用者。仓库当前聚焦于：

- 多源市场上下文采集
- 持仓优先的风险检查
- 覆盖 OKX 合约可交易品种的热度排名
- 面向 Telegram 的可读汇报
- 适配 Hermes / OpenClaw 的 skill 打包方式

本仓库**不负责自动交易、下单、收益承诺或投资建议**。如果连接真实 OKX 账户，请只使用**只读权限**凭据。

## 它解决什么问题

很多市场监控原型停留在“拉回一堆原始数据”，却没有把真正关键的问题回答出来：

- *我现在的持仓是否需要立刻关注？*
- *今天的风险到底来自宏观事件、加密原生事件，还是交易所层面的仓位变化？*
- *除了持仓之外，现在还有哪些 OKX 可交易标的值得继续盯？*
- *如何把这些结果整理成几秒钟能读完的一条消息？*

OKX 市场哨兵的做法是：通过 Phase3 主流程，把多源数据先沉淀为统一产物，再从中生成通知摘要、触发候选和 dashboard 所需载荷。

## 实际输出长什么样

典型的用户侧输出可以是这样：

```text
OKX 市场哨兵｜扫描完成
• 状态：正常
• 重点持仓：BTC, ETH
• 市场偏置：bearish
• 风险等级：high
• 是否升级深度分析：是
• 观察级触发：macro event window, holdings pressure

风险触发摘要
宏观风险共振      : 已触发
持仓安全事件      : 无
持仓事件簇        : 已触发
是否升级深度审查  : 是
观察级触发        : macro event window, holdings pressure

值得继续盯的品种
• 当前短名单：BTC, ETH, SOL, DOGE
• 来自已有持仓：BTC, ETH
• 来自社媒热度：SOL, DOGE
• 来自 OKX OI 异动：ETH, SOL

风险持仓
1. BTC | risk=high | events=2 | heat=18 | drivers=macro event window, holdings event cluster
2. ETH | risk=medium | events=1 | heat=11 | drivers=open-interest change

热门可交易品种
1. SOL | score=82 | source=social momentum + OKX OI changes | why=high social heat; leading open-interest move
2. DOGE | score=71 | source=social momentum | why=multi-account consensus
```

## 看板预览

如果你想先看成品，而不是先读代码，可以直接看这里：

<img width="2560" height="5960" alt="image" src="https://github.com/user-attachments/assets/8c2545a2-14c3-4718-89dc-cc83cc5f59e6" />

## 核心功能

- [x] **Phase3 主流程**：统一完成抓取、聚合与触发器生成
- [x] **持仓优先风险视图**：先回答“手里仓位有没有事”
- [x] **OKX-first 热度排名**：覆盖 OKX 合约可交易品种，而不只是主流现货币种
- [x] **宏观 + 加密原生事件聚合**：避免把交易所事故、黑客事件或结构性风险淹没在普通资讯流里
- [x] **Telegram 通知流**：输出简洁、可读、便于运营的监控摘要
- [x] **本地 dashboard**：用于查看市场状态、触发状态和热榜结果
- [x] **可复用 skill 包**：`skills/crypto-market-sentinel/` 可直接给 Hermes / OpenClaw 类运行时使用
- [x] **Semantic Compass 维护流程**：支持持续更新风险短语包与语义提取规则

## 技术栈

- **语言**：Python 3.10+
- **项目形态**：可运行参考实现 + 可复用 agent skill 包
- **Agent 集成**：兼容 Hermes / OpenClaw 的 skill 目录结构
- **决策范式**：artifact-first、rules-first 的监控主链路，辅以 agent 协助的语义维护
- **核心依赖**：`requests`、`PyYAML`、`mcp`
- **质量工具**：`pytest`、`ruff`
- **外部系统 / API**：OKX 数据接口、Telegram Bot API、Jin10 MCP，以及通过环境变量配置的新闻/社媒来源

## 兼容性（Compatibility）

这个仓库有两种主要使用方式：

1. **作为可运行的 Python 项目**：本地执行监控流程、dashboard 和 notifier
2. **作为 skill 仓库**：给 **Hermes**、**OpenClaw** 等 agent 运行时加载

可复用的 skill 包位于：

```text
skills/crypto-market-sentinel/
```

## 快速开始

### 环境要求

- Python 3.10+
- 你计划接入的数据源所需的网络访问能力
- 可选：OKX 只读 API 凭据
- 可选：Telegram Bot 凭据
- 可选：Hermes / OpenClaw（如果你要直接加载 skill）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API 密钥

先创建本地环境文件：

```bash
cp .env.example .env
```

然后编辑 `.env`，只填你实际需要的变量即可。当前主流程通常通过**本地 OKX CLI / profile** 读取交易所数据；环境变量主要用于通知发送和可选上游接入：

```dotenv
# OKX（如果你的本地接入方式需要，保留只读凭据即可）
OKX_API_KEY=
OKX_API_SECRET=
OKX_PASSPHRASE=
OKX_IS_PAPER_TRADING=true

# Telegram notifier
TELEGRAM_BOT_TOKEN=
PHASE3_NOTIFY_TELEGRAM_BOT_TOKEN=
PHASE3_NOTIFY_TELEGRAM_CHAT_ID=

# Optional upstreams
OPENNEWS_TOKEN=
TWITTER_TOKEN=
OPEN_TOKEN=
BLOCKBEATS_API_KEY=
JIN10_MCP_TOKEN=
CMC_API_KEY=
```

### 运行项目

运行 Phase3 主流程：

```bash
python scripts/phase3_pipeline.py
```

启动本地 dashboard：

```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

然后打开：

```text
http://127.0.0.1:8765
```

生成一条 Telegram 风格的监控摘要：

```bash
python scripts/run_phase3_notifier.py
```

如需实际发送通知，请配置 `PHASE3_NOTIFY_TELEGRAM_CHAT_ID`；如果你希望通知脚本使用独立机器人，也可以额外设置 `PHASE3_NOTIFY_TELEGRAM_BOT_TOKEN` 覆盖默认的 `TELEGRAM_BOT_TOKEN`。

通过 agent brief 刷新 Semantic Compass：

```bash
python scripts/refresh_semantic_compass.py --brief "补充霍尔木兹海峡关闭 / 恢复通航 / 交易所宕机 / 稳定币脱锚等表达"
```

### 只安装 Skill 包

如果你只想复用 skill，不打算把整套参考实现跑起来，可以直接复制 skill 目录。

Hermes：

```bash
mkdir -p ~/.hermes/skills/market-monitoring && cp -r skills/crypto-market-sentinel ~/.hermes/skills/market-monitoring/
```

OpenClaw：

```bash
mkdir -p ~/.agents/skills/market-monitoring && cp -r skills/crypto-market-sentinel ~/.agents/skills/market-monitoring/
```

## 使用示例

### 1. 生成核心产物

```bash
python scripts/phase3_pipeline.py
```

典型输出：

```text
context/context_cache.json
context/trigger_candidates.json
reports/phase3_report_*.md
```

### 2. 运行通知脚本

```bash
python scripts/run_phase3_notifier.py
```

### 3. 运行测试

```bash
pytest -q
```

## 仓库结构

```text
.
├── config/                              # 风险规则与语义配置
├── dashboard/                           # 本地 dashboard 服务与静态前端
├── docs/                                # 架构、流程、Schema 与交接文档
├── scripts/                             # Phase3 主流程、notifier 与各类 source fetcher
├── skills/crypto-market-sentinel/       # 可复用 skill 包
├── tests/                               # 回归与打包测试
├── .env.example                         # 本地环境变量模板
├── requirements.txt                     # 快速启动用依赖清单
├── README.md                            # 英文说明
└── README.zh.md                         # 中文说明
```

## 我应该先看哪个文件？

- **我想先跑整套系统** → 从 `README.zh.md` 和 `scripts/phase3_pipeline.py` 开始
- **我只关心 skill 复用** → 先看 `skills/crypto-market-sentinel/README.zh.md`
- **我想快速理解架构** → 看 `docs/phase3-overview.md` 和 `skills/crypto-market-sentinel/references/architecture.md`
- **我想找运行命令** → 看 `skills/crypto-market-sentinel/references/runtime-commands.md`
- **我想看 dashboard 入口** → 看 `dashboard/server.py`

## 项目亮点

- **双重交付形态**：不是单纯的文档仓库，也不是一堆零散脚本，而是既能本地运行、又能作为 skill 复用的完整项目
- **用户可读输出优先**：重视 dashboard 和 Telegram 摘要的可读性，而不是只堆原始 JSON
- **边界清晰**：专注监控、风险识别与 watchlist 生成，不假装自己是执行引擎
- **OKX 原生视角更强**：热榜逻辑建立在 OKX 可交易品种和交易所原生仓位变化之上
- **语义层可持续维护**：Semantic Compass 让风险短语与事件标签具备持续演进能力

## 依赖说明（Dependencies）

常用或必需依赖包括：

- `python`
- `requests`
- `PyYAML`
- `mcp`
- `pytest`
- `ruff`
- `okx` CLI（可选，取决于你的本地集成方式）
- `hermes` CLI（可选，用于语义刷新与 agent 相关工作流）
- Telegram Bot API 凭据（可选，用于通知推送）

## 项目状态与范围

当前仓库以 **Phase3 风险哨兵主链路** 为唯一产品主线，重点包括：

- 多源抓取器
- 统一上下文缓存
- 触发候选生成
- dashboard 汇报
- Telegram notifier 输出
- 供 agent 复用的 skill 打包

本仓库有意**不包含**自动下单执行逻辑。

## 安全说明

- 不要提交真实 API Key、Bot Token 或账户密钥
- `.env` 只用于本地开发
- 优先使用只读 OKX 凭据
- 除非你自己补上鉴权和网络隔离，否则不要把 dashboard 直接暴露到公网
- 对外发布前请先阅读 `SECURITY.md`

## 社区协作

欢迎围绕文档、测试、打包与监控能力改进发起 issue 或 PR。涉及敏感信息时，请遵循 `SECURITY.md` 中的披露方式。

## 许可证

MIT License
