[English](README.md) | [中文](README.zh.md)

# OKX 市场哨兵 Skill

## 概述

这是一个面向 OKX 市场监控与 Agent Skill 工作流的非官方 Python 市场哨兵示例，适用于 OpenClaw、Hermes 等支持 AgentSkills 风格 skill 目录的 agent 系统。

本项目旨在为用户提供一种构建加密市场监控系统的参考方案。该系统能够周期性收集 OKX 市场数据、OKX 新闻、账户/持仓信息、宏观市场数据、加密新闻、社交热度以及语义风险短语，并将这些信息聚合为统一的市场上下文缓存和触发器候选结果。用户可以在此基础上编写自定义监控逻辑、风险规则、通知策略、dashboard 展示逻辑，或将其作为 OpenClaw / Hermes 的外部 skill 使用。

本项目不直接提供自动交易、下单、盈利策略、投资建议或任何收益保证。强烈建议用户仅在研究、模拟监控或只读 API 环境中使用。如果接入真实 OKX 账户，请仅使用只读权限 API Key，不建议授予交易权限。

本项目与 OKX 官方交易机器人功能无关。如需使用 OKX 官方提供的网格、DCA、套利等交易机器人，请参考 OKX 官方交易机器人产品。

---

## 实际运行出来是什么样

如果你不是来研究代码，而是想先知道“这玩意最后会发什么给用户”，可以先看一个真实风格的通知模板。

```text
OKX 市场哨兵｜运行完成
• 状态: 正常
• 持仓: BTC, ETH
• 方向偏置: bearish
• 风险等级: high
• LLM 唤醒: 是
• 观察级触发: macro_event_window, held_symbol_pressure

Trigger 判定
宏观四因子共振 : 已触发
持仓安全事件   : 无
持仓事件簇     : 已触发
LLM 唤醒       : 是
观察级触发     : macro_event_window, held_symbol_pressure

热度排名
• 当前列表: BTC, ETH, SOL, DOGE
• 持仓优先: BTC, ETH
• 白名单热议: SOL, DOGE
• OKX持仓异动: ETH, SOL

持仓风险
1. BTC ｜ risk=high ｜ events=2 ｜ heat=18 ｜ reasons=macro_event_window, held_symbol_cluster
2. ETH ｜ risk=medium ｜ events=1 ｜ heat=11 ｜ reasons=oi_change

热门可交易品种
1. SOL ｜ 评分=82 ｜ 来源=社媒热议 + OKX持仓异动 ｜ 原因=社媒高热；OI异动靠前
2. DOGE ｜ 评分=71 ｜ 来源=社媒热议 ｜ 原因=多账户共识
```

你可以把这个项目简单理解成：

- 平时默默扫市场
- 先看你手里持仓有没有事
- 再给你一份当前值得继续盯的标的列表
- 最后把结果整理成一段 Telegram / agent 能直接消费的消息

## 入门

### 先决条件

Python 版本：>= 3.10  
建议使用 Python 虚拟环境运行本项目。

### Dependencies

基础依赖：

- `python` >= 3.10
- `requests`
- `PyYAML`
- `pytest`
- `ruff`

可选依赖：

- OKX API Key，只读权限即可
- `okx` CLI（如果你的本地工作流依赖 OKX 相关命令行集成）
- `hermes` CLI，用于 Semantic Compass 自动刷新
- OpenClaw，用于 skill 加载与 agent 集成
- Telegram Bot Token，用于风险通知推送

如果仓库中已经提供 `requirements.txt`，请优先使用：

```bash
pip install -r requirements.txt
```

如果暂未提供完整依赖文件，可先安装最小运行依赖：

```bash
pip install requests PyYAML pytest
```

---

## 快速入门

如果你只想先装上去，不想看一大堆解释，先看这两行：

### OpenClaw
```bash
openclaw skills install <your-skill-slug>
```

### Hermes
```bash
mkdir -p ~/.hermes/skills/market-monitoring && cp -r skills/crypto-market-sentinel ~/.hermes/skills/market-monitoring/
```

如果这个 skill 还没正式发布到 ClawHub，那么 OpenClaw 先用本地目录方式也可以：

```bash
mkdir -p ~/.agents/skills/market-monitoring && cp -r skills/crypto-market-sentinel ~/.agents/skills/market-monitoring/
```

如果你要把它发到 ClawHub，公开文档支持的发布命令是：

```bash
npm i -g clawhub && clawhub login && clawhub skill publish ./skills/crypto-market-sentinel --slug <your-skill-slug> --name "OKX Market Sentinel" --version 0.1.0 --tags latest
```

也可以直接走网页入口：`https://clawhub.ai/publish-skill`

如果你不是只想装 skill，而是想把整套参考实现本地跑起来，再继续下面这些步骤。

创建并激活 Python 虚拟环境。

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows：

```bash
python -m venv .venv
.venv\Scripts\activate
```

安装依赖项。

```bash
pip install -U pip
pip install -r requirements.txt
```

如果当前版本暂未提供 `requirements.txt`，可先安装基础依赖：

```bash
pip install requests PyYAML pytest
```

检查配置文件。主要配置位于：

```text
config/phase3_rules.yaml
config/semantic_compass.json
skills/crypto-market-sentinel/templates/dashboard_settings.example.json
```

如需读取 OKX 账户或持仓信息，请在本地环境变量或 `.env` 文件中配置 OKX API 凭据。建议仅使用只读权限 API Key。

```bash
OKX_API_KEY=***
OKX_API_SECRET=***
OKX_PASSPHRASE=<your_passphrase>
OKX_IS_PAPER_TRADING=true
```

如需启用 Telegram 通知，请配置：

```bash
TELEGRAM_BOT_TOKEN=<your_...ken>
TELEGRAM_CHAT_ID=<your_telegram_chat_id>
```

运行市场哨兵主流程。

```bash
python scripts/phase3_pipeline.py
```

该命令会依次执行数据源抓取、上下文聚合和触发器生成，并将结果写入本地 `context/` 目录。

启动本地 dashboard。

```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

然后在浏览器中打开：

```text
http://127.0.0.1:8765
```

如果您希望通过 Telegram 接收通知，可以运行：

```bash
python scripts/run_phase3_notifier.py
```

如果您希望使用 Hermes 帮助刷新 Semantic Compass，可以运行：

```bash
python scripts/semantic_compass.py
```

运行测试：

```bash
pytest -q
```

---

## 监控对象及运行模式

本项目默认不执行交易，也不会自动下单。它的核心用途是市场监控、风险识别、上下文聚合和 agent 触发器生成。

### Local Pipeline Mode

本地管线模式会读取配置文件，抓取多个数据源，并生成统一的市场上下文文件。

```bash
python scripts/phase3_pipeline.py
```

主要输出：

```text
context/context_cache.json
context/trigger_candidates.json
reports/
```

### Dashboard Mode

Dashboard 模式会启动一个本地 HTTP 服务，用于展示市场状态、风险摘要、触发器候选结果和配置状态。

```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

默认建议只绑定 `127.0.0.1`。如果需要暴露到局域网或公网，请自行添加鉴权、反向代理和访问控制。

### Telegram Notifier Mode

通知模式会运行市场哨兵流程，并在检测到重要变化时推送 Telegram 消息。

```bash
python scripts/run_phase3_notifier.py
```

该模式适合定时任务、cron job 或长期运行的轻量监控环境。

### Agent Skill Mode

本项目包含：

```text
skills/crypto-market-sentinel/SKILL.md
skills/crypto-market-sentinel/references/
skills/crypto-market-sentinel/templates/
```

可作为 OpenClaw / Hermes 等 agent 的 skill 目录使用。Agent 可以读取 `SKILL.md`，根据 references 中的说明理解如何运行市场哨兵、查看 dashboard、读取 context cache 或解释 trigger candidates。

Hermes 示例安装路径：

```bash
mkdir -p ~/.hermes/skills/market-monitoring
cp -r skills/crypto-market-sentinel ~/.hermes/skills/market-monitoring/
```

OpenClaw 用户可参考：

```text
OPENCLAW_SETUP.md
```

Hermes 用户可参考：

```text
HERMES_SETUP.md
```

### Semantic Compass Mode

Semantic Compass 用于维护风险语义短语包，例如地缘风险、交易所风险、监管风险、重大新闻风险和降温短语等。

配置文件位于：

```text
config/semantic_compass.json
```

运行刷新：

```bash
python scripts/semantic_compass.py
```

该模式适合让 agent 根据最新市场语言和新闻语境，持续调整风险匹配短语。

---

## Compatibility

这个仓库当前主要面向以下几类使用方式：

- **Hermes**：可以作为本地 skill + 可运行参考实现直接使用
- **OpenClaw**：可以作为 skill 目录接入，并按仓库中的说明进行集成
- **其他 agent runtime**：可以参考本仓库的结构、脚本与配置，自行适配

它不是某个单一 runtime 的官方插件，而是一个更偏向可复用、可改造的市场监控 skill 仓库。

---

## 配置说明

### phase3_rules.yaml

`config/phase3_rules.yaml` 存储主要市场哨兵规则，包括：

- 数据过期时间
- 事件窗口
- 风险关键词
- 新闻风险阈值
- 社交热度阈值
- 市场上下文阈值
- 触发器生成规则

用户可以根据自己的交易品种、风险偏好和监控目标修改这些参数。

### semantic_compass.json

`config/semantic_compass.json` 存储语义风险短语包，包括：

- `geo_risk`
- `news_risk`
- `regulatory_risk`
- `exchange_risk`
- cooldown phrases
- severity anchors

该文件用于帮助系统识别新闻和文本中的风险语义，而不只是依赖固定关键词。

### dashboard_settings.example.json

Dashboard 设置模板位于：

```text
skills/crypto-market-sentinel/templates/dashboard_settings.example.json
```

建议复制为本地设置文件后再修改，避免直接改动模板文件。

---

## 输出

运行主流程后，终端可能输出类似内容：

```text
RUN SOURCE okx_market_fetch ... OK
RUN SOURCE okx_news_fetch ... OK
RUN SOURCE okx_positions_fetch ... OK
RUN SOURCE macro_fetch ... OK
RUN SOURCE crypto_news_fetch ... OK
RUN SOURCE social_heat_fetch ... OK

BUILD CONTEXT CACHE
context/context_cache.json written

BUILD TRIGGER CANDIDATES
context/trigger_candidates.json written

==== Market Sentinel Summary ====
Time: 2026-05-05 14:37:21
Mode: local pipeline
Primary Exchange: OKX
Market State: neutral
Macro Risk: medium
Crypto News Risk: medium
Geo Risk: low
Social Heat: elevated

Watched Instruments:
- BTC-USDT-SWAP
- ETH-USDT-SWAP
- SOL-USDT-SWAP

Hot Symbols:
1. BTC
2. ETH
3. SOL
4. DOGE
5. XRP

Wake Triggers: 2
Observe Only Triggers: 5
Context Cache: context/context_cache.json
Trigger Candidates: context/trigger_candidates.json
==== End of Summary ====

WAKE BTC-USDT-SWAP
Reason: market volatility increased while related news risk is medium

OBSERVE_ONLY ETH-USDT-SWAP
Reason: price movement is notable but risk score is below wake threshold
```

启动 dashboard 后，终端可能输出：

```text
Serving dashboard at http://127.0.0.1:8765
GET /api/dashboard
GET /api/context
GET /api/triggers
```

运行 Telegram notifier 后，可能输出：

```text
RUNNING PHASE3 PIPELINE
LOADING PREVIOUS SNAPSHOT
BUILDING CHANGE SUMMARY
SENDING TELEGRAM MESSAGE
NOTIFIER DONE
```

---

## 项目结构

```text
okx-market-sentinel-skill/
├── config/
│   ├── phase3_rules.yaml
│   └── semantic_compass.json
├── dashboard/
│   ├── server.py
│   └── dashboard_adapter.py
├── docs/
├── scripts/
│   ├── phase3_pipeline.py
│   ├── build_context_cache.py
│   ├── build_triggers.py
│   ├── run_phase3_notifier.py
│   ├── semantic_compass.py
│   └── sources/
├── skills/
│   └── crypto-market-sentinel/
│       ├── SKILL.md
│       ├── references/
│       └── templates/
├── tests/
├── HERMES_SETUP.md
├── OPENCLAW_SETUP.md
├── README.md
└── README.zh.md
```

---

## 安全说明

请勿将以下内容提交到 GitHub：

```text
.env
OKX API Key
Telegram Bot Token
context/
reports/
本地缓存文件
账户持仓文件
```

建议：

- OKX API Key 只开启只读权限
- 不要给本项目授予交易权限
- 不要在公网直接暴露 dashboard
- 如果必须暴露 dashboard，请添加鉴权和反向代理
- 不要把真实账户截图、持仓、API 凭据写入 issue 或 commit
- 定期检查 `.gitignore` 和 `.clawhubignore`

更多安全信息可参考 `SECURITY.md`。

---

## 测试

运行全部测试：

```bash
pytest -q
```

运行单个测试文件：

```bash
pytest tests/test_phase3_pipeline.py -q
pytest tests/test_dashboard_server.py -q
pytest tests/test_semantic_compass.py -q
```

建议在提交代码前运行：

```bash
pytest -q
ruff check .
```

---

## 使用场景

本项目适合以下场景：

- 构建加密市场风险监控系统
- 为 OpenClaw / Hermes 提供市场监控 skill
- 聚合 OKX 市场数据与外部新闻数据
- 生成 agent 可读取的 context cache
- 生成 wake / observe_only 类型触发器
- 构建 Telegram 风险提醒
- 构建本地 dashboard
- 研究 agent 如何参与交易前的信息收集与风险判断

本项目不适合以下场景：

- 直接自动下单
- 高频交易
- 做市执行
- 资金托管
- 无人工监督的真实账户交易
- 任何保证收益的交易系统

---

## 声明

本项目是非官方项目，与 OKX 官方无直接关系。

本项目仅用于展示、研究和开发 agent skill 工作流，不构成投资建议、交易建议或金融服务。本项目不保证数据完整性、实时性、准确性，也不保证任何交易收益。

使用者应自行评估市场风险、API 权限风险、系统故障风险和信息延迟风险。任何基于本项目产生的交易、投资或账户操作，均由使用者自行承担责任。

---

## License

本仓库使用 MIT License。详见 `LICENSE`。
