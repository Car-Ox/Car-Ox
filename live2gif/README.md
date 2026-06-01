# LiveToGif

将 Apple Live Photo (.heic + .mov) 转换为高质量 GIF 动图。

## 依赖

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/)（需安装并添加到系统 PATH）

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### Python API

```python
from src.converter import convert_mov_to_gif

# 默认参数：15 FPS，最大 480px，无限循环
convert_mov_to_gif("input.mov", "output.gif")

# 自定义参数
convert_mov_to_gif(
    input_path="input.mov",
    output_path="output.gif",
    fps=10,
    max_size=320,
    loop=False,
    max_colors=128,   # 调色板颜色数（不传则默认 256）
)
```

### 命令行 (CLI)

```bash
# 单文件转换（支持 .mov 或 .heic）
python main.py IMG_1234.heic

# 指定输出目录
python main.py IMG_1234.heic -o ./gifs

# 自定义帧率和尺寸
python main.py IMG_1234.mov -r 24 -s 720

# 高质量 + 非循环
python main.py IMG_1234.heic --quality high --no-loop

# 批量转换目录（支持递归）
python main.py ./Photos --recursive --verbose
```

### 图形界面 (GUI)

```bash
python main_gui.py
```

## 转换原理

采用 FFmpeg 双通道调色板模式，在画质和文件体积间取得平衡：

```
MOV → 帧提取 → 调色板生成 → 调色板应用 → GIF
```

滤镜链：

```
fps={N}, scale=min(W,iw):min(H,ih), split[a][b];
[a]palettegen[=max_colors=N][p];
[b][p]paletteuse
```
> 注意：FFmpeg 7.0+ 将 `max_colors` 选项从 `paletteuse` 移至 `palettegen`。

## 测试

### 运行所有测试

```bash
# 在项目根目录（live2gif/）运行
python -m pytest tests/ -v
```

### 运行特定模块测试

```bash
# 仅核心转换模块
python -m pytest tests/test_converter.py -v

# 仅输入解析模块
python -m pytest tests/test_input_resolver.py -v

# 仅 CLI 模块
python -m pytest tests/test_cli.py -v

# 仅 GUI 模块
python -m pytest tests/test_gui.py -v
```

### 测试分类说明

| 标记 | 说明 | 运行方式 |
|------|------|---------|
| （无标记） | 单元测试，始终运行 | `pytest tests/` |
| `@pytest.mark.ffmpeg` | FFmpeg 集成测试，需要系统安装 FFmpeg | 有 FFmpeg 时自动包含，无则自动跳过 |

### FFmpeg 集成测试

当系统安装了 FFmpeg 时，以下集成测试会自动运行：

- 使用真实 FFmpeg 将测试 MOV 转换为 GIF
- 验证输出 GIF 尺寸不超过 max_size 限制
- 验证损坏文件输入抛出 ConversionError
- 验证 fps、loop、max_colors 参数正确传递
- 验证输出文件为有效 GIF 格式（GIF89a/GIF87a 魔术字节）

当 FFmpeg 未安装时，这些测试自动跳过（不视为失败）。

### 生成覆盖率报告

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 从源码构建（macOS）

### 本地构建

在 Mac 上运行以下脚本，一键构建 `Live2Gif.app` 和 `.dmg` 安装镜像：

```bash
chmod +x build_macos.sh
./build_macos.sh
```

**前置条件：**
- macOS 11.0+
- Python 3.10+（推荐 3.11）
- [Homebrew](https://brew.sh)（用于安装 FFmpeg）

**脚本做了什么：**
1. 检测系统环境（macOS / Python / Homebrew）
2. 安装依赖 + PyInstaller
3. 安装 FFmpeg（如未安装）
4. PyInstaller 构建 `.app` Bundle（含 bundled FFmpeg）
5. 配置 Info.plist（文件类型关联 .heic / .mov）
6. 创建 `.dmg` 安装镜像

**产物位置：**
- `dist/Live2Gif.app` — 可直接双击运行
- `Live2Gif.dmg` — 可分发的安装镜像

### CI 自动构建（GitHub Actions）

Push 到 `main` 分支或手动触发时，自动在 `macos-latest` 运行器上构建。

→ 详见 [.github/workflows/build-macos.yml](.github/workflows/build-macos.yml)

构建产物（`.dmg`）在 Actions 页面的 Artifacts 中下载，保留 30 天。

## 下载安装包

### GitHub Releases（推荐）

从 [Releases](../../releases) 页面下载最新 `Live2Gif.dmg`。

安装步骤：
1. 打开 `Live2Gif.dmg`
2. 将 `Live2Gif.app` 拖入 `Applications` 文件夹
3. 首次运行时，右键 → "打开" 以绕过 Gatekeeper
4. （可选）右键任意 `.heic` 或 `.mov` 文件 → "打开方式" → Live2Gif

### 应用图标

`assets/icon.icns` 用于 .app 图标。当前使用默认图标，可替换为自定义图标。
详见 [assets/README.md](assets/README.md)。

## 项目结构

```
live2gif/
├── .github/workflows/
│   └── build-macos.yml       # GitHub Actions — macOS 自动构建
├── assets/
│   ├── icon.icns             # macOS 应用图标（可选，见 assets/README.md）
│   └── README.md             # 图标制作说明
├── src/
│   ├── __init__.py           # 公共 API
│   ├── converter.py          # 核心转换逻辑 (FFmpeg 调色板)
│   ├── input_resolver.py     # 输入解析 (.heic → .mov 映射)
│   ├── cli.py                # 命令行界面 (argparse)
│   └── gui.py                # 图形界面 (Tkinter)
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # 全局夹具与 FFmpeg 检测
│   ├── test_converter.py     # 转换模块测试 (单元 + FFmpeg 集成)
│   ├── test_input_resolver.py # 输入解析测试
│   ├── test_cli.py           # CLI 测试
│   └── test_gui.py           # GUI 测试
├── main.py                   # CLI 启动入口
├── main_gui.py               # GUI 启动入口
├── build_macos.sh            # macOS 本地构建脚本
├── requirements.txt
└── README.md
```

## 许可

MIT
