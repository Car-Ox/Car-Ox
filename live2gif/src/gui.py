"""LiveToGif 图形用户界面。

使用 Tkinter 构建跨平台 GUI，支持文件选择、参数调节、异步转换。
GUI 层与核心逻辑完全分离，只负责界面和调用。
"""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.converter import convert_mov_to_gif, ConversionError
from src.input_resolver import resolve_input, InputError


class LiveToGifGUI:
    """LiveToGif 主窗口。

    提供文件选择、转换参数调节、异步转换和进度反馈功能。

    Attributes:
        root: Tkinter 根窗口。
        input_file: 当前选择的输入文件路径。
        fps: 当前帧率设置。
        max_size: 当前最大尺寸设置。
        quality: 当前质量预设。
        loop: 是否无限循环。
    """

    def __init__(self, root: tk.Tk | None = None) -> None:
        """初始化主窗口。

        Args:
            root: 可选的 Tk 根窗口，None 时自动创建。
        """
        self.root = root or tk.Tk()
        self.root.title("Live2Gif")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        # 状态
        self._input_file: str = ""
        self._thread: threading.Thread | None = None
        self._queue: queue.Queue[tuple[str, str]] = queue.Queue()

        self._create_widgets()
        self._start_queue_poller()

    # ── 部件创建 ────────────────────────────────────────────────────

    def _create_widgets(self) -> None:
        """创建所有 UI 部件。"""
        # 文件选择区域
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill=tk.X)

        ttk.Label(file_frame, text="Live Photo 文件:").pack(anchor=tk.W)

        self._select_btn = ttk.Button(
            file_frame, text="选择文件...", command=self._select_file
        )
        self._select_btn.pack(side=tk.LEFT, padx=(0, 10))

        self._file_label = ttk.Label(
            file_frame, text="点击「选择文件」选择 .mov 或 .heic 文件", foreground="gray"
        )
        self._file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 设置区域
        settings_frame = ttk.LabelFrame(self.root, text="转换设置", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # 帧率滑块
        fps_frame = ttk.Frame(settings_frame)
        fps_frame.pack(fill=tk.X)
        ttk.Label(fps_frame, text="帧率 (FPS):").pack(side=tk.LEFT)
        self._fps_var = tk.IntVar(value=15)
        self._fps_slider = tk.Scale(
            fps_frame, from_=1, to=30, orient=tk.HORIZONTAL,
            variable=self._fps_var, length=200,
        )
        self._fps_slider.pack(side=tk.LEFT, padx=10)
        self._fps_label = ttk.Label(fps_frame, text="15", width=3)
        self._fps_label.pack(side=tk.LEFT)
        # 滑块值变化时更新标签
        self._fps_slider.configure(
            command=lambda v: self._fps_label.configure(text=str(int(float(v))))
        )

        # 最大尺寸 + 质量
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(row2, text="最大边长:").pack(side=tk.LEFT)
        self._size_var = tk.StringVar(value="480")
        self._size_entry = ttk.Entry(row2, textvariable=self._size_var, width=6)
        self._size_entry.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(row2, text="质量:").pack(side=tk.LEFT)
        self._quality_var = tk.StringVar(value="")
        self._quality_combo = ttk.Combobox(
            row2, textvariable=self._quality_var,
            values=["low", "medium", "high"],
            state="readonly", width=10,
        )
        self._quality_combo.pack(side=tk.LEFT, padx=5)

        # 循环复选框
        self._loop_var = tk.BooleanVar(value=True)
        self._loop_cb = ttk.Checkbutton(
            settings_frame, text="无限循环", variable=self._loop_var,
        )
        self._loop_cb.pack(anchor=tk.W, pady=(5, 0))

        # 转换按钮
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=tk.X)

        self._convert_btn = ttk.Button(
            btn_frame, text="转换为 GIF", command=self._start_conversion,
        )
        self._convert_btn.pack()

        # 进度条（不确定模式）
        self._progress_bar = ttk.Progressbar(
            self.root, mode="indeterminate", length=300,
        )
        self._progress_bar.pack(pady=(5, 0))

        # 状态标签
        self._status_label = ttk.Label(self.root, text="就绪", foreground="gray")
        self._status_label.pack(pady=(2, 10))

    # ── 参数提取属性 ────────────────────────────────────────────────

    @property
    def fps(self) -> int:
        """当前帧率设置值。"""
        return self._fps_var.get()

    @property
    def max_size(self) -> int:
        """当前最大边长设置值。"""
        return int(self._size_var.get())

    @property
    def quality(self) -> str | None:
        """当前质量预设，未选择时返回 None。"""
        val = self._quality_var.get()
        return val if val else None

    @property
    def loop(self) -> bool:
        """是否启用无限循环。"""
        return self._loop_var.get()

    @property
    def input_file(self) -> str:
        """当前选择的输入文件路径。"""
        return self._input_file

    # ── 文件选择 ────────────────────────────────────────────────────

    def _select_file(self) -> None:
        """打开文件选择对话框，支持 .mov 和 .heic。"""
        path = filedialog.askopenfilename(
            title="选择 Live Photo",
            filetypes=[
                ("Live Photo 文件", "*.mov *.heic"),
                ("MOV 视频", "*.mov"),
                ("HEIC 照片", "*.heic"),
                ("所有文件", "*.*"),
            ],
        )
        if path:
            self._input_file = path
            self._file_label.configure(text=path, foreground="black")

    # ── 转换流程 ────────────────────────────────────────────────────

    def _start_conversion(self) -> None:
        """启动转换流程（在主线程中调用）。

        检查输入文件，弹出保存对话框，然后在后台线程中执行转换。
        """
        if not self._input_file:
            messagebox.showerror("错误", "请先选择要转换的文件。")
            return

        # 弹出保存对话框
        stem = Path(self._input_file).stem
        output = filedialog.asksaveasfilename(
            title="保存 GIF",
            defaultextension=".gif",
            filetypes=[("GIF 动图", "*.gif"), ("所有文件", "*.*")],
            initialfile=f"{stem}.gif",
        )
        if not output:
            return  # 用户取消

        # 禁用 UI
        self._convert_btn.configure(state=tk.DISABLED)
        self._select_btn.configure(state=tk.DISABLED)
        self._progress_bar.start(10)
        self._status_label.configure(text="转换中...", foreground="black")

        # 在主线程中读取所有 Tkinter 变量（线程安全）
        params = {
            "input_path": self._input_file,
            "output_path": output,
            "fps": self.fps,
            "max_size": self.max_size,
            "loop": self.loop,
            "max_colors": _quality_to_colors(self.quality),
        }

        # 后台线程执行转换
        self._thread = threading.Thread(
            target=self._run_conversion, args=(params,), daemon=True,
        )
        self._thread.start()

    def _run_conversion(self, params: dict) -> None:
        """在后台线程中执行 FFmpeg 转换。

        Args:
            params: 转换参数字典（已在主线程中读取完毕）。
        """
        try:
            convert_mov_to_gif(**params)
            self._queue.put(("success", params["output_path"]))
        except (ConversionError, InputError, Exception) as e:
            self._queue.put(("error", str(e)))

    def _process_queue(self) -> None:
        """处理消息队列（由 Tkinter after 定时调用）。

        在主线程中安全地更新 UI。
        """
        try:
            while True:
                msg_type, data = self._queue.get_nowait()
                if msg_type == "success":
                    self._reset_ui()
                    self._status_label.configure(text="✅ 转换完成", foreground="green")
                    messagebox.showinfo("转换完成", f"GIF 已保存至:\n{data}")
                    self._reveal_in_file_manager(data)
                elif msg_type == "error":
                    self._reset_ui()
                    self._status_label.configure(text="❌ 转换失败", foreground="red")
                    messagebox.showerror("转换失败", data)
        except queue.Empty:
            pass

    def _reset_ui(self) -> None:
        """重置 UI 到就绪状态。"""
        self._convert_btn.configure(state=tk.NORMAL)
        self._select_btn.configure(state=tk.NORMAL)
        self._progress_bar.stop()

    def _start_queue_poller(self) -> None:
        """启动队列轮询（每 100ms 检查一次）。"""
        self._process_queue()
        self.root.after(100, self._start_queue_poller)

    # ── 平台工具 ────────────────────────────────────────────────────

    @staticmethod
    def _reveal_in_file_manager(filepath: str) -> None:
        """在系统文件管理器中显示文件。

        macOS: 在 Finder 中选中文件。
        Windows: 在资源管理器中选中文件。

        Args:
            filepath: 要显示的文件的完整路径。
        """
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", filepath])
        else:
            subprocess.run(["explorer", "/select,", str(Path(filepath))])

    # ── 启动 ────────────────────────────────────────────────────────

    def run(self) -> None:
        """启动 Tkinter 主事件循环。"""
        self.root.mainloop()


# ── 辅助函数 ────────────────────────────────────────────────────────

def _quality_to_colors(quality: str | None) -> int | None:
    """将质量字符串映射为 max_colors 数值。

    Args:
        quality: "low" / "medium" / "high" 或 None。

    Returns:
        max_colors 值，None 表示使用默认。
    """
    if quality is None:
        return None
    mapping = {"low": 64, "medium": 128, "high": 256}
    return mapping.get(quality)
