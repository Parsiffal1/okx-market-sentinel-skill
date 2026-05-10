[English](README.md) | [中文](README.zh.md)

# Crypto Market Sentinel Skill

这个目录是 OKX 市场哨兵项目中**可复用的 skill 包**。

如果你只想看 agent 侧的操作指导，从这里开始即可；如果你还想把整套参考实现跑起来，请回到仓库根目录阅读主 README。

## 这个 skill 适合做什么

当你希望 agent 协助以下事项时，使用这个 skill：

- 运行 Phase3 市场监控主流程
- 审查持仓优先的风险逻辑
- 理解热度排名产物与触发结果
- 启动或排查 dashboard / notifier 流程
- 维护 Semantic Compass 风险短语包
- 将项目打包迁移到其他 agent 环境

## 关键文件

- `SKILL.md` — 主操作契约
- `references/architecture.md` — 架构分层与系统说明
- `references/runtime-commands.md` — 标准运行、测试、dashboard 命令
- `templates/dashboard_settings.example.json` — dashboard 配置模板

## 它和完整仓库的关系

这个 skill 目录只是项目的一部分；真正可运行的参考实现还在仓库根目录：

- `scripts/`
- `dashboard/`
- `config/`
- `docs/`
- `tests/`

## 推荐阅读顺序

1. `SKILL.md`
2. `references/runtime-commands.md`
3. `references/architecture.md`
4. 需要完整上手时再看仓库根目录 `README.md` / `README.zh.md`
