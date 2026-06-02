"""GUI 模块的单元测试。

严格遵循 TDD：每个测试先于实现代码编写。
测试 Tkinter GUI 的构造、参数提取、文件选择、转换流程。
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from src.gui import LiveToGifGUI


# ── 测试辅助 ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tk_root():
    """创建模块级 Tk 根窗口，所有 GUI 测试复用同一个实例。

    使用模块级别作用域的原因：
    - conda 自带的 Tcl/Tk 在连续创建多个 tk.Tk() 实例后会资源耗尽
    - 复用单个 Tk 实例避免了 "Can't find a usable tk.tcl" 错误
    - 配合 _cleanup_tk_children autouse fixture 清理测试残留部件
    """
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk 不可用（conda Tcl 资源限制），跳过 GUI 测试。")
    yield root
    _cleanup_tk_children(root)
    try:
        root.destroy()
    except tk.TclError:
        pass


def _cleanup_tk_children(root: tk.Tk) -> None:
    """递归销毁 root 下所有子部件，保持测试间隔离。"""
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except tk.TclError:
            pass


@pytest.fixture(autouse=True)
def _cleanup_after_test(tk_root: tk.Tk) -> None:
    """每次测试后清理 root 下的残留部件，确保测试间隔离。

    因为 tk_root 是模块级 fixture（复用同一个 Tk 实例），
    需要一个函数级 autouse fixture 在每次测试后清理上一个测试留下的部件。
    """
    yield
    _cleanup_tk_children(tk_root)


# ── GUI 构造测试 ────────────────────────────────────────────────────

class TestGUIConstruction:
    """窗口和部件构造测试。"""

    def test_window_title(self, tk_root: tk.Tk) -> None:
        """主窗口标题应为 Live2Gif。"""
        app = LiveToGifGUI(root=tk_root)
        assert tk_root.title() == "Live2Gif"

    def test_window_not_resizable(self, tk_root: tk.Tk) -> None:
        """窗口应不可调整大小。"""
        app = LiveToGifGUI(root=tk_root)
        # resizable() 无参数返回 (width_bool, height_bool)
        w, h = tk_root.resizable()
        assert not w and not h

    def test_file_label_exists(self, tk_root: tk.Tk) -> None:
        """文件路径标签应存在且默认为占位文本。"""
        app = LiveToGifGUI(root=tk_root)
        text = app._file_label.cget("text")
        assert any(kw in text for kw in ("选择", "点击", "文件"))

    def test_select_button_exists(self, tk_root: tk.Tk) -> None:
        """选择文件按钮应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._select_btn is not None

    def test_fps_slider_exists(self, tk_root: tk.Tk) -> None:
        """帧率滑块应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._fps_slider is not None

    def test_max_size_entry_exists(self, tk_root: tk.Tk) -> None:
        """最大尺寸输入框应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._size_entry is not None

    def test_quality_combo_exists(self, tk_root: tk.Tk) -> None:
        """质量下拉框应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._quality_combo is not None

    def test_loop_checkbox_exists(self, tk_root: tk.Tk) -> None:
        """循环复选框应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._loop_var is not None

    def test_convert_button_exists(self, tk_root: tk.Tk) -> None:
        """转换按钮应存在，文本包含'转换'。"""
        app = LiveToGifGUI(root=tk_root)
        assert "转换" in app._convert_btn.cget("text")

    def test_progress_bar_exists(self, tk_root: tk.Tk) -> None:
        """不确定模式进度条应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._progress_bar is not None

    def test_status_label_exists(self, tk_root: tk.Tk) -> None:
        """状态标签应存在。"""
        app = LiveToGifGUI(root=tk_root)
        assert app._status_label is not None


# ── 默认参数测试 ────────────────────────────────────────────────────

class TestDefaultParameters:
    """部件默认值测试。"""

    def test_default_fps(self, tk_root: tk.Tk) -> None:
        """帧率滑块默认为 15。"""
        app = LiveToGifGUI(root=tk_root)
        assert app.fps == 15

    def test_default_max_size(self, tk_root: tk.Tk) -> None:
        """最大尺寸默认 480。"""
        app = LiveToGifGUI(root=tk_root)
        assert app.max_size == 480

    def test_default_quality_none(self, tk_root: tk.Tk) -> None:
        """质量默认不设置（None）。"""
        app = LiveToGifGUI(root=tk_root)
        assert app.quality is None

    def test_default_loop_enabled(self, tk_root: tk.Tk) -> None:
        """循环默认开启（True）。"""
        app = LiveToGifGUI(root=tk_root)
        assert app.loop is True

    def test_default_input_file_empty(self, tk_root: tk.Tk) -> None:
        """初始输入文件路径为空字符串。"""
        app = LiveToGifGUI(root=tk_root)
        assert app.input_file == ""


# ── 参数提取测试 ────────────────────────────────────────────────────

class TestParameterExtraction:
    """从部件提取用户设置参数测试。"""

    def test_fps_reads_from_slider(self, tk_root: tk.Tk) -> None:
        """fps 属性应从滑块读取当前值。"""
        app = LiveToGifGUI(root=tk_root)
        app._fps_slider.set(24)
        assert app.fps == 24

    def test_max_size_reads_from_entry(self, tk_root: tk.Tk) -> None:
        """max_size 应从输入框读取整数值。"""
        app = LiveToGifGUI(root=tk_root)
        app._size_var.set("720")
        assert app.max_size == 720

    def test_max_size_invalid_input_returns_default(self, tk_root: tk.Tk) -> None:
        """用户输入非数字文本时 max_size 应安全回退到 480。"""
        app = LiveToGifGUI(root=tk_root)
        app._size_var.set("abc")
        assert app.max_size == 480  # 默认值安全回退

    def test_max_size_empty_string_returns_default(self, tk_root: tk.Tk) -> None:
        """用户清空输入框时 max_size 应安全回退到 480。"""
        app = LiveToGifGUI(root=tk_root)
        app._size_var.set("")
        assert app.max_size == 480  # 默认值安全回退

    def test_quality_reads_from_combo(self, tk_root: tk.Tk) -> None:
        """quality 应从下拉框读取当前选择。"""
        app = LiveToGifGUI(root=tk_root)
        app._quality_var.set("high")
        assert app.quality == "high"

    def test_loop_false_when_checkbox_unchecked(self, tk_root: tk.Tk) -> None:
        """取消勾选时 loop 为 False。"""
        app = LiveToGifGUI(root=tk_root)
        app._loop_var.set(False)
        assert app.loop is False

    def test_fps_range_boundaries(self, tk_root: tk.Tk) -> None:
        """滑块范围应为 1 到 30。"""
        app = LiveToGifGUI(root=tk_root)
        slider = app._fps_slider
        assert int(slider.cget("from")) == 1
        assert int(slider.cget("to")) == 30


# ── 文件选择测试 ────────────────────────────────────────────────────

class TestFileSelection:
    """文件选择对话框测试。"""

    def test_select_file_updates_label(self, tk_root: tk.Tk) -> None:
        """选择文件后应更新路径标签。"""
        app = LiveToGifGUI(root=tk_root)
        test_path = str(Path("/test/IMG_1234.heic"))

        with patch("tkinter.filedialog.askopenfilename", return_value=test_path):
            app._select_file()

        assert test_path in app._file_label.cget("text")

    def test_select_sets_input_file(self, tk_root: tk.Tk) -> None:
        """选择文件后应更新 input_file 属性。"""
        app = LiveToGifGUI(root=tk_root)
        test_path = str(Path("/test/IMG_1234.mov"))

        with patch("tkinter.filedialog.askopenfilename", return_value=test_path):
            app._select_file()

        assert app.input_file == test_path

    def test_select_cancelled_does_nothing(self, tk_root: tk.Tk) -> None:
        """取消选择时不应修改状态。"""
        app = LiveToGifGUI(root=tk_root)
        original_text = app._file_label.cget("text")

        with patch("tkinter.filedialog.askopenfilename", return_value=""):
            app._select_file()

        assert app.input_file == ""
        assert app._file_label.cget("text") == original_text

    def test_file_dialog_filters(self, tk_root: tk.Tk) -> None:
        """文件对话框应过滤 .mov 和 .heic。"""
        app = LiveToGifGUI(root=tk_root)

        with patch("tkinter.filedialog.askopenfilename", return_value="/t.mov") as mock_dlg:
            app._select_file()
            call_kwargs = mock_dlg.call_args.kwargs
            filetypes = call_kwargs.get("filetypes", [])
            patterns = " ".join(str(ft) for ft in filetypes)
            assert ".mov" in patterns or ".heic" in patterns


# ── 转换流程测试 ────────────────────────────────────────────────────

# 所有转换测试共享的基础 mock
_CONVERSION_MOCKS = [
    patch("src.gui.convert_mov_to_gif"),
    patch("src.gui.resolve_input", side_effect=lambda p: str(p)),
    patch("src.gui.subprocess.run"),  # 阻止 explorer/open 弹出
]


class TestConversionFlow:
    """转换执行流程测试。"""

    @pytest.fixture
    def app_with_file(self, tk_root: tk.Tk, tmp_path: Path) -> LiveToGifGUI:
        """创建一个已选择文件的 GUI 实例。"""
        mov = tmp_path / "test.mov"
        mov.touch()
        app = LiveToGifGUI(root=tk_root)
        app._input_file = str(mov)
        return app

    def test_conversion_disables_button(self, app_with_file: LiveToGifGUI) -> None:
        """转换开始时应禁用转换按钮。"""
        with patch("tkinter.filedialog.asksaveasfilename", return_value="/o.gif"), \
             patch("src.gui.convert_mov_to_gif"), \
             patch("src.gui.subprocess.run"):
            app_with_file._start_conversion()
            state = str(app_with_file._convert_btn.cget("state"))
            assert state == tk.DISABLED

    def test_conversion_starts_progress_bar(self, app_with_file: LiveToGifGUI) -> None:
        """转换开始时应启动进度条。"""
        with patch("tkinter.filedialog.asksaveasfilename", return_value="/o.gif"), \
             patch("src.gui.convert_mov_to_gif"), \
             patch("src.gui.subprocess.run"):
            app_with_file._start_conversion()
            mode = str(app_with_file._progress_bar.cget("mode"))
            assert mode == "indeterminate"

    def test_conversion_updates_status(self, app_with_file: LiveToGifGUI) -> None:
        """转换开始时应更新状态标签。"""
        with patch("tkinter.filedialog.asksaveasfilename", return_value="/o.gif"), \
             patch("src.gui.convert_mov_to_gif"), \
             patch("src.gui.subprocess.run"):
            app_with_file._start_conversion()
            status = app_with_file._status_label.cget("text")
            assert "转换中" in status or "转换" in status

    def test_conversion_fails_without_input(self, tk_root: tk.Tk) -> None:
        """无输入文件时点击转换应显示错误。"""
        app = LiveToGifGUI(root=tk_root)

        with patch("tkinter.messagebox.showerror") as mock_err:
            app._start_conversion()
            mock_err.assert_called_once()
            assert "文件" in mock_err.call_args.args[1]

    def test_successful_conversion_shows_message(
        self, app_with_file: LiveToGifGUI
    ) -> None:
        """转换成功应显示提示框。"""
        with patch("src.gui.convert_mov_to_gif"), \
             patch("src.gui.subprocess.run"), \
             patch("tkinter.filedialog.asksaveasfilename", return_value="/o.gif"), \
             patch("tkinter.messagebox.showinfo") as mock_info:
            app_with_file._start_conversion()
            # 等待后台线程完成
            if app_with_file._thread:
                app_with_file._thread.join(timeout=2)
            app_with_file._process_queue()
            assert mock_info.called

    def test_conversion_error_shows_message(
        self, app_with_file: LiveToGifGUI
    ) -> None:
        """转换失败应显示错误框。"""
        from src.converter import ConversionError

        with patch("src.gui.convert_mov_to_gif",
                   side_effect=ConversionError("测试错误")), \
             patch("src.gui.subprocess.run"), \
             patch("tkinter.filedialog.asksaveasfilename", return_value="/o.gif"), \
             patch("tkinter.messagebox.showerror") as mock_err:
            app_with_file._start_conversion()
            if app_with_file._thread:
                app_with_file._thread.join(timeout=2)
            app_with_file._process_queue()
            mock_err.assert_called_once()

    def test_conversion_uses_thread(self, app_with_file: LiveToGifGUI) -> None:
        """转换应在后台线程中执行。"""
        def _check_thread(*args, **kwargs):
            return None

        with patch("src.gui.convert_mov_to_gif", side_effect=_check_thread), \
             patch("src.gui.subprocess.run"), \
             patch("tkinter.filedialog.asksaveasfilename", return_value="/o.gif"):
            app_with_file._start_conversion()
            app_with_file._thread.join(timeout=2)
            assert not app_with_file._thread.is_alive()

    def test_output_save_dialog_called(self, app_with_file: LiveToGifGUI) -> None:
        """转换前应弹出保存对话框。"""
        with patch("src.gui.convert_mov_to_gif"), \
             patch("src.gui.subprocess.run"), \
             patch("tkinter.filedialog.asksaveasfilename") as mock_save:
            mock_save.return_value = ""
            app_with_file._start_conversion()
            mock_save.assert_called_once()

    def test_save_cancelled_aborts_conversion(self, app_with_file: LiveToGifGUI) -> None:
        """取消保存对话框时应中止转换。"""
        with patch("src.gui.convert_mov_to_gif") as mock_convert, \
             patch("src.gui.subprocess.run"), \
             patch("tkinter.filedialog.asksaveasfilename", return_value=""):
            app_with_file._start_conversion()
            mock_convert.assert_not_called()


# ── 平台工具测试 ────────────────────────────────────────────────────

class TestPlatformUtilities:
    """平台特定工具函数测试。"""

    def test_open_in_finder_macos(self, tk_root: tk.Tk) -> None:
        """macOS 上应在 Finder 中打开文件所在目录。"""
        app = LiveToGifGUI(root=tk_root)

        with patch("sys.platform", "darwin"), \
             patch("subprocess.run") as mock_run:
            app._reveal_in_file_manager("/path/to/output.gif")
            mock_run.assert_called_once()
            cmd = mock_run.call_args.args[0]
            assert "open" in cmd
            assert "-R" in cmd

    def test_open_in_explorer_windows(self, tk_root: tk.Tk) -> None:
        """Windows 上应在资源管理器中选中文件。"""
        app = LiveToGifGUI(root=tk_root)

        with patch("sys.platform", "win32"), \
             patch("subprocess.run") as mock_run:
            app._reveal_in_file_manager(r"C:\out.gif")
            mock_run.assert_called_once()
            cmd = mock_run.call_args.args[0]
            assert "explorer" in cmd
            # /select, 是 Windows explorer 参数
            assert any("/select," in str(c) for c in cmd)


# ── _MEIPASS 兼容性测试 ─────────────────────────────────────────────

class TestPyInstallerCompat:
    """PyInstaller 打包兼容性测试。"""

    def test_runs_without_meipass(self, tk_root: tk.Tk) -> None:
        """无 _MEIPASS 属性时正常创建（开发模式）。"""
        app = LiveToGifGUI(root=tk_root)
        assert app is not None

    def test_runs_with_mock_meipass(self, tk_root: tk.Tk) -> None:
        """有 sys._MEIPASS 时也正常创建（打包模式）。"""
        with patch.object(sys, "_MEIPASS", "/fake/app/Contents/Resources", create=True):
            app = LiveToGifGUI(root=tk_root)
            assert app is not None
