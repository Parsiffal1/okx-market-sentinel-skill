[English](README.md) | [中文](README.zh.md)

# Crypto Market Sentinel Skill

这个目录是 Crypto Market Sentinel 项目的 **skill 包**。

如果你只想复用 skill 指导，从这里开始即可；如果你还想要完整可运行代码，请回到仓库根目录查看 `scripts/`、`dashboard/`、`config/`、`tests/`。

## 这个 skill 能帮助你做什么

- 持仓优先市场监控
- OKX-first 热门可交易品种排名
- 宏观 + 加密原生风险聚合
- dashboard + Telegram 汇报流程
- cron 友好、低 token 运行方式
- 基于 **Semantic Compass** 的语义短语包维护

## 关键文件

- `SKILL.md` — 主 skill 契约
- `references/architecture.md` — 系统设计总览
- `references/runtime-commands.md` — 常用运行 / 测试 / dashboard 命令
- `templates/dashboard_settings.example.json` — dashboard 设置模板

## 适用场景

当你想做这些事情时，使用这个 skill：

- 把风险哨兵适配到自己的环境
- 审查风险模型与唤醒条件
- 部署 dashboard / notifier 栈
- 把项目整理成 agent skill，而不是一堆零散脚本

## 如果你还要完整代码

回到仓库根目录，重点查看：

- `scripts/`
- `dashboard/`
- `config/`
- `tests/`
- `docs/`
