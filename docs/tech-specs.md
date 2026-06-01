# 🔧 技术规范文档

## 技术栈

| 层级 | 技术选型 | 版本要求 |
|------|---------|---------|
| 语言 | Python | 3.10+ |
| GUI 框架 | PySide6 / PyQt6 | 6.5+ |
| 视频处理 | FFmpeg (通过 subprocess) | 5.0+ |
| 打包工具 | PyInstaller | 5.0+ |
| 测试框架 | pytest | 7.0+ |
| CI/CD | GitHub Actions | - |
| 代码格式化 | Black + isort | - |
| 代码检查 | Ruff / Flake8 | - |
| 类型检查 | mypy (strict mode) | - |

---

## 项目结构

```
livetogif/
├── src/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── ui/                  # GUI 模块
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── widgets/
│   │   └── resources/
│   ├── core/                # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── converter.py     # GIF 转换引擎
│   │   ├── livephoto.py     # Live Photo 解析
│   │   └── batch.py         # 批量处理
│   ├── utils/               # 工具函数
│   │   ├── __init__.py
│   │   ├── ffmpeg.py        # FFmpeg 封装
│   │   └── metadata.py      # 元数据处理
│   └── resources/           # 应用资源
├── tests/
│   ├── __init__.py
│   ├── test_converter.py
│   ├── test_livephoto.py
│   └── fixtures/            # 测试用 Live Photo 文件
├── docs/                    # 项目文档
├── .devlogs/                # 开发日志
├── .github/
│   └── workflows/
│       └── ci.yml           # CI 配置
├── skills/                  # 项目技能文件
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

---

## 核心架构

### 转换管道 (Conversion Pipeline)

```
Live Photo (.MOV+.HEIC)
    → LivePhotoParser (解析/验证)
    → FrameExtractor (FFmpeg 提取帧)
    → FrameProcessor (调色/缩放/优化)
    → GifEncoder (GIF 编码)
    → 输出文件
```

### 模块间通信

- UI 层通过信号/槽 (Qt Signals/Slots) 与核心模块通信
- 批量处理通过 `QThread` 工作线程执行
- FFmpeg 通过 `subprocess` 异步调用

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
