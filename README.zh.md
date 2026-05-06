[English](README.md) | [中文](README.zh.md)

# Crypto Market Sentinel Skill 仓库

这是一个面向 **Hermes**、**OpenClaw 风格 skill** 与普通开发者的 **OKX-first 市场风险哨兵 + 热门可交易品种监控 skill 仓库**。

它不是只有一个 `SKILL.md` 的提示词仓库，而是把：

1. **可复用的 skill 层**
2. **可运行的参考实现层**

打包在一个仓库里，方便其他用户直接复用、改造和部署。

## 这个仓库是什么

这个仓库由两层组成：

1. **Skill 层**：位于 `skills/crypto-market-sentinel/`
2. **参考实现层**：位于 `scripts/`、`dashboard/`、`config/`、`tests/`

也就是说，别人不仅可以读取 skill 指南，还可以直接看到并运行完整实现。

## 适合谁使用

- 想要 **OKX-first 风险哨兵**，而不是完整交易框架的用户
- 想把市场风险监控能力封装成 **agent skill** 的开发者
- 需要以下能力的人：
  - 持仓优先监控
  - 宏观 + 加密原生风险聚合
  - 热门可交易品种排名
  - dashboard + Telegram 汇报
  - 低 token、cron 友好运行方式

## 你能得到什么

- Skill 入口：
  - `skills/crypto-market-sentinel/SKILL.md`
- Skill 文档：
  - `skills/crypto-market-sentinel/README.md`
  - `skills/crypto-market-sentinel/README.zh.md`
  - `skills/crypto-market-sentinel/references/`
  - `skills/crypto-market-sentinel/templates/`
- 可运行的参考实现：
  - `scripts/`
  - `dashboard/`
  - `config/`
  - `tests/`
- 项目文档：
  - `docs/`

## 快速开始

### 1. 先读 skill
建议先看：

- `skills/crypto-market-sentinel/SKILL.md`

然后再看：

- `skills/crypto-market-sentinel/README.zh.md`
- `skills/crypto-market-sentinel/references/architecture.md`
- `skills/crypto-market-sentinel/references/runtime-commands.md`

### 2. 运行参考实现
```bash
python scripts/phase3_pipeline.py
python scripts/run_phase3_notifier.py
```

### 3. 启动 dashboard
```bash
python dashboard/server.py --host 127.0.0.1 --port 8765
```

## 兼容性

这个仓库被设计成 **skill + 可运行参考实现** 的混合形态。

- **Hermes**：支持作为本地 skill 使用，也支持完整参考项目运行
- **OpenClaw 风格 skill 布局**：通过 `skills/crypto-market-sentinel/` 子树与单行 frontmatter 元数据兼容
- **其他 agent runtime**：更适合手工集成 skill 子目录与仓库根目录脚本

它不是某个单一 runtime 的 in-process 插件 SDK，而是一个可复用 skill 包 + 外部脚本/文档/参考实现。

## 依赖说明

真实运行依赖不止一个 Python 解释器。

### 必需
- `python`
- 运行这些脚本所需的 Python 依赖

### 常见 OKX-first 工作流必需
- `okx` CLI（OKX market / news / positions fetchers 会用到）

### Semantic Compass 刷新必需
- `hermes` CLI（用于 agent 驱动的语义短语包刷新）

### 可选 / 视环境而定
- Telegram notifier 所需凭据
- `OPENNEWS_TOKEN`、`TWITTER_TOKEN`、`OPEN_TOKEN` 等 source token
- 可访问配置中声明的上游数据源

## 安装方式

### Hermes
把本仓库 clone 下来，或把 skill 子目录复制到 Hermes skills 目录。

典型目录：

```bash
~/.hermes/skills/market-monitoring/crypto-market-sentinel/
```

至少应复制：

- `skills/crypto-market-sentinel/SKILL.md`
- `skills/crypto-market-sentinel/references/`
- `skills/crypto-market-sentinel/templates/`

如果你还想要可运行的实现，不要只复制 skill 子目录，而应保留整个仓库。

### OpenClaw 风格 skill 布局
这个仓库遵循当前流行 skill 仓库的常见结构：

- 根 README
- `skills/<skill-name>/SKILL.md`
- 可选 `references/`、`templates/`、额外 setup 文档

后续若要适配 ClawHub / OpenClaw 风格发布，会比较顺滑。

### 手工安装 / 其他 agent
把 `skills/crypto-market-sentinel/` 看作 skill 包，把仓库根目录看作参考实现。

## 仓库结构

```text
skills/
  crypto-market-sentinel/
    SKILL.md
    README.md
    README.zh.md
    references/
    templates/

dashboard/
scripts/
config/
tests/
docs/
README.md
README.zh.md
```

## 推荐使用流程

1. 阅读 `skills/crypto-market-sentinel/SKILL.md`
2. 阅读 `skills/crypto-market-sentinel/references/`
3. 查看 `scripts/` 与 `dashboard/` 里的参考实现
4. 运行 `pytest -q`
5. 运行 `python scripts/phase3_pipeline.py`
6. 按自己的环境替换数据源、通知与 dashboard 部署方式

## 我应该先看哪个文件？

- 只想看 skill 契约 → `skills/crypto-market-sentinel/SKILL.md`
- 想看安装说明 → `skills/crypto-market-sentinel/README.zh.md`
- 想看架构总览 → `skills/crypto-market-sentinel/references/architecture.md`
- 想看运行命令 → `skills/crypto-market-sentinel/references/runtime-commands.md`
- 想看真正实现 → `scripts/`、`dashboard/`、`config/`

## 项目状态与范围

这个仓库 **不是**：

- 自动下单交易框架
- 完整量化平台
- 通用执行引擎

它 **是**：

> 一个 OKX-first 的市场风险哨兵 + 热门可交易品种监控 skill，并且附带可运行的参考实现。

## 测试

```bash
pytest -q
```

## 许可证

本仓库采用 MIT License，见 `LICENSE`。
