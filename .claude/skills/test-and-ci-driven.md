---
name: test-and-ci-driven
description: Use when writing pytest tests, mocking FFmpeg/subprocess/tkinter, configuring GitHub Actions CI/CD, or setting up multi-platform test matrices
---

# 测试驱动开发与 CI/CD

## 测试金字塔

```
        ┌─────┐
        │ E2E │  FFmpeg 集成测试 (@pytest.mark.ffmpeg)
        ├─────┤
       ┌┤ GUI │   Tkinter 组件测试 (module级 tk_root fixture)
       │├─────┤
       ││ CLI │   argparse + main 端到端
       │├─────┤
       ││单元 │  converter, input_resolver 纯函数测试
       └┴─────┘
```

## pytest 夹具模式

### 自动跳过未安装的依赖

```python
# conftest.py
import shutil
import pytest

def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ffmpeg: 需要 FFmpeg 的集成测试")

def pytest_collection_modifyitems(config, items):
    if ffmpeg_available():
        return
    skip_ffmpeg = pytest.mark.skip(reason="FFmpeg 未安装")
    for item in items:
        if "ffmpeg" in item.keywords:
            item.add_marker(skip_ffmpeg)
```

### Tkinter module 级 fixture（避免 Tcl 资源耗尽）

```python
@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk 不可用")
    yield root
    # 清理子部件
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except tk.TclError:
            pass
    root.destroy()
```

### FFmpeg 测试视频生成

```python
@pytest.fixture(scope="module")
def test_mov(ffmpeg_path: str, test_media_dir: Path) -> Path:
    output = test_media_dir / "test_video.mov"
    cmd = [ffmpeg_path, "-f", "lavfi", "-i",
           "testsrc=duration=0.5:size=64x64:rate=10",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(output)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return output
```

## Mock 模式

### Mock subprocess.run

```python
from unittest.mock import patch

with patch("src.converter.subprocess.run") as mock_run:
    convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"))
    call_args = mock_run.call_args[0][0]
    assert "palettegen" in call_args[call_args.index("-vf") + 1]
```

### Mock subprocess 异常

```python
# CalledProcessError
error = subprocess.CalledProcessError(1, ["ffmpeg"], stderr=b"fail")
mock_run.side_effect = error

# TimeoutExpired
error = subprocess.TimeoutExpired(["ffmpeg"], timeout=300)
mock_run.side_effect = error

# FileNotFoundError
error = FileNotFoundError(2, "No such file", "ffmpeg")
mock_run.side_effect = error
```

### Mock Tkinter 对话框

```python
with patch("tkinter.filedialog.askopenfilename", return_value="/test.mov"):
    app._select_file()

with patch("tkinter.messagebox.showerror") as mock_err:
    app._start_conversion()
    mock_err.assert_called_once()
```

## GitHub Actions CI 工作流

### macOS 构建 + 测试

```yaml
name: Build macOS App
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-macos:
    runs-on: macos-latest
    defaults:
      run:
        working-directory: live2gif
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt pyinstaller
      - run: brew install ffmpeg
      - run: python -m pytest tests/ -v --ignore=tests/test_gui.py
      - run: |
          pyinstaller --windowed --name Live2Gif \
            --add-binary="$(which ffmpeg):." \
            --osx-bundle-identifier=com.livetogif.app main_gui.py
      - run: hdiutil create -volname "Live2Gif" \
            -srcfolder dist/Live2Gif.app -ov -format UDZO Live2Gif.dmg
      - uses: actions/upload-artifact@v4
        with:
          name: Live2Gif-macOS
          path: live2gif/Live2Gif.dmg
          retention-days: 30
```

## 测试命令

```bash
# 全部测试
python -m pytest tests/ -v

# 排除 GUI（CI 无显示器）
python -m pytest tests/ -v --ignore=tests/test_gui.py

# 仅 FFmpeg 集成测试
python -m pytest tests/ -v -m ffmpeg

# 覆盖率
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 常见模式

| 场景 | 方案 |
|------|------|
| 需要真实 FFmpeg | `@pytest.mark.ffmpeg` + conftest 自动跳过 |
| 需要 Tk 显示 | module级 `tk_root` fixture |
| 测试批量 CLI | mock `convert_mov_to_gif` + `resolve_input` |
| 测试异常路径 | `side_effect` 模拟各种异常 |
| CI 中跳过 GUI | `--ignore=tests/test_gui.py` |
