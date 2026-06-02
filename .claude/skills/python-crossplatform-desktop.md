---
name: python-crossplatform-desktop
description: Use when building Python desktop apps with Tkinter, managing cross-platform paths, running FFmpeg via subprocess, or PyInstaller bundling on macOS/Windows
---

# Python 跨平台桌面开发

## 核心原则

使用 Python 标准库中的跨平台组件，最小化平台依赖。

## Tkinter 模式

### 线程安全的 UI 更新

```python
import queue
import threading
import tkinter as tk

class App:
    def __init__(self, root):
        self._queue: queue.Queue = queue.Queue()
        self._start_queue_poller()

    def _start_queue_poller(self) -> None:
        """每 100ms 轮询队列，主线程中安全更新 UI。"""
        try:
            while True:
                msg_type, data = self._queue.get_nowait()
                if msg_type == "success":
                    self._on_success(data)
                elif msg_type == "error":
                    self._on_error(data)
        except queue.Empty:
            pass
        self.root.after(100, self._start_queue_poller)

    def _run_task(self, params: dict) -> None:
        """后台线程执行耗时操作。"""
        try:
            result = do_work(**params)
            self._queue.put(("success", result))
        except Exception as e:
            self._queue.put(("error", str(e)))
```

### Tkinter 变量线程安全

始终在主线程读取 Tkinter 变量，后台线程只使用已读取的快照：

```python
# ✅ 正确：在主线程中快照变量
params = {
    "fps": self._fps_var.get(),      # 主线程读取
    "size": int(self._size_var.get()),
}
thread = threading.Thread(target=self._run_task, args=(params,))
thread.start()

# ❌ 错误：后台线程直接读取 Tk 变量
thread = threading.Thread(target=lambda: do_work(fps=self._fps_var.get()))
```

## 路径处理

### 唯一规则：用 Path，不用字符串拼接

```python
from pathlib import Path

# ✅ 跨平台自动适配
output = Path(dir) / f"{Path(input).stem}.gif"
output.mkdir(parents=True, exist_ok=True)
```

### subprocess.run 跨平台注意事项

```python
import subprocess
import sys

# Windows 需要 .exe 后缀
ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"

# 始终添加 timeout 防止挂起
result = subprocess.run(
    cmd, check=True, capture_output=True, text=True, timeout=300
)
```

## PyInstaller 打包

### 检测打包模式

```python
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # PyInstaller 打包模式
    resource_dir = Path(sys._MEIPASS)
else:
    # 开发模式
    resource_dir = Path(__file__).parent
```

### macOS 添加二进制文件

```bash
pyinstaller --windowed --name Live2Gif \
    --add-binary="$(which ffmpeg):." \
    --osx-bundle-identifier=com.app.name \
    main_gui.py
```

## 平台特定操作

### 文件管理器中显示文件

```python
if sys.platform == "darwin":
    subprocess.run(["open", "-R", filepath])
else:
    # Windows: /select, 后紧跟路径（不含空格分隔）
    subprocess.run(["explorer", "/select," + str(Path(filepath))])
```

## 常见陷阱

| 陷阱 | 修复 |
|------|------|
| `tk.Tk()` 多次创建导致 Tcl 资源耗尽 | module 级 fixture 复用单例 |
| Tkinter 变量跨线程访问 | 主线程快照后传给后台线程 |
| Windows `explorer /select,` 参数分隔 | `/select,path` 作为一个参数 |
| `subprocess.run` 无超时导致挂起 | 始终设置 `timeout=300` |
| `Path.exists()` 对目录也返回 True | 额外检查 `Path.is_file()` |
