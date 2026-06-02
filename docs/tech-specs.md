# 🔧 技术规范文档

## 技术栈

| 层级 | 技术选型 | 版本要求 |
|------|---------|---------|
| 语言 | Python | 3.10+ |
| GUI 框架 | Tkinter (Python 标准库) | 内置 |
| 视频处理 | FFmpeg (通过 subprocess) | 5.0+ |
| 打包工具 | PyInstaller | 5.0+ |
| 测试框架 | pytest | 7.0+ |
| CI/CD | GitHub Actions | - |
| 代码检查 | Ruff | - |
| 类型检查 | mypy (strict mode) | - |

---

## 项目结构

```
live2gif/
├── src/
│   ├── __init__.py           # 公共 API 导出
│   ├── converter.py          # GIF 转换引擎 (FFmpeg 双通道调色板)
│   ├── input_resolver.py     # Live Photo (.heic → .mov) 路径解析
│   ├── cli.py                # 命令行界面 (argparse + 批量处理)
│   ├── gui.py                # 图形界面 (Tkinter + 线程队列)
│   └── quality_presets.py    # CLI/GUI 共享质量预设
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # 全局夹具 + FFmpeg 检测
│   ├── test_converter.py     # 转换器测试 (单元 + 集成)
│   ├── test_input_resolver.py
│   ├── test_cli.py
│   ├── test_gui.py
│   └── test_quality_presets.py
├── main.py                   # CLI 入口
├── main_gui.py               # GUI 入口
├── docs/                     # 项目文档
├── .devlogs/                 # 开发日志
├── .github/workflows/        # CI 配置
├── assets/                   # 图标等静态资源
├── pyproject.toml
└── README.md
```

---

## 核心架构

### 转换管道 (Conversion Pipeline)

```
Live Photo (.heic)
    → InputResolver (解析 → 同名 .mov)
    → FFmpeg 双通道调色板 (palettegen → paletteuse)
    → GIF 输出
```

### 模块间通信

- UI 层通过线程安全队列 (`queue.Queue`) 与核心模块通信
- 批量处理通过 `ThreadPoolExecutor` 工作线程池执行
- FFmpeg 通过 `subprocess` 同步调用（带超时保护）

---

## API 设计原则

- 核心模块与 UI 完全解耦
- 所有公共方法必须有类型注解
- 错误处理使用自定义异常类
- 使用 Python `pathlib.Path` 处理所有路径

---

## 编码规范

- 遵循 PEP 8，行长限制 100 字符
- 类名：PascalCase，函数/变量：snake_case
- 私有方法前缀 `_`，内部模块前缀 `_`
- 每个公共函数/类必须有 docstring (Google 风格)
- 类型注解 100% 覆盖
