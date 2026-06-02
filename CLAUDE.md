# CLAUDE.md — LiveToGif 项目指引

> 本文件为 Claude Code 提供项目上下文、工作规范和标准文件路径指引。

---

## 📂 项目标准文件路径

| 文件 | 路径 | 说明 |
|------|------|------|
| **开发需求** | [docs/requirements.md](docs/requirements.md) | 功能需求、非功能需求、用户故事 |
| **技术规范** | [docs/tech-specs.md](docs/tech-specs.md) | 技术栈、项目结构、架构设计、编码规范 |
| **设计规范** | [docs/design-specs.md](docs/design-specs.md) | UI 布局、色彩系统、交互规范、无障碍 |
| **执行步骤** | [docs/execution-steps.md](docs/execution-steps.md) | 各阶段任务清单、关键决策记录 |
| **开发日志** | [.devlogs/](.devlogs/) | 每日开发日志（模板: `.devlogs/template.md`） |

---

## 🎯 项目概要

- **名称：** LiveToGif
- **目标：** 将 Apple Live Photo 转换为高质量 GIF 动图
- **平台：** macOS（主）/ Windows（辅）
- **技术栈：** Python 3.10+ / Tkinter / FFmpeg

---

## 📐 工作规范

### 开始任何开发任务前

1. **阅读需求** — 参考 [docs/requirements.md](docs/requirements.md) 确认功能范围
2. **检查技术规范** — 参考 [docs/tech-specs.md](docs/tech-specs.md) 确认架构和编码规范
3. **查看执行步骤** — 参考 [docs/execution-steps.md](docs/execution-steps.md) 了解当前阶段和任务上下文
4. **参考设计** — 涉及 UI 时参考 [docs/design-specs.md](docs/design-specs.md)

### 完成开发任务后

1. **更新执行步骤** — 在 [docs/execution-steps.md](docs/execution-steps.md) 中勾选已完成项
2. **记录开发日志** — 在 [.devlogs/](.devlogs/) 中更新当日日志（自动模板）
3. **记录关键决策** — 如有技术决策变更，更新执行步骤中的决策记录表

### 编码规范

- **语言：** 所有注释和文档使用中文，代码标识符使用英文
- **TDD：** 先写测试，再写实现（遵循 `test-and-ci-driven` skill）
- **类型注解：** 所有公共 API 必须有完整类型注解
- **模块解耦：** 核心逻辑与 UI 完全分离

---

## 🛠 项目技能 (Skills)

本项目使用以下专业技能，通过 `Skill` 工具调用：

| 序号 | 技能名称 | 用途 | 触发场景 |
|------|---------|------|---------|
| 1 | `python-crossplatform-desktop` | Python 跨平台桌面开发 | GUI 开发、Tkinter 组件 |
| 2 | `ffmpeg-mastery` | FFmpeg 视频处理 | 视频转换、GIF 编码 |
| 3 | `macos-app-packaging` | macOS 应用打包 | .app Bundle、DMG、签名 |
| 4 | `test-and-ci-driven` | 测试驱动与 CI | TDD 流程、GitHub Actions |

---

## 🔄 每日开发日志

每次开发会话结束时，系统会自动提醒更新开发日志。

- **模板：** [.devlogs/template.md](.devlogs/template.md)
- **日志目录：** [.devlogs/](.devlogs/)
- **命名规则：** `YYYY-MM-DD.md`
