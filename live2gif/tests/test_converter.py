"""convert_mov_to_gif 函数的单元测试与集成测试。

严格遵循 TDD：每个测试先于实现代码编写。

测试分为两类：
1. 单元测试 — mock FFmpeg，验证命令行构造和错误处理
2. 集成测试 — 需要系统安装 FFmpeg（标记 @pytest.mark.ffmpeg）
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from src.converter import convert_mov_to_gif, ConversionError
from tests.conftest import ffmpeg_available

# 辅助：mock resolve_input，让输入原样返回（测试不关心解析逻辑）
_RESOLVE = patch("src.converter.resolve_input", side_effect=lambda p: str(Path(p)))


class TestConvertMovToGif:
    """convert_mov_to_gif 完整测试套件。"""

    # ── 命令行构造测试 ──────────────────────────────────────────

    def test_ffmpeg_command_default_params(self) -> None:
        """使用默认参数时应构造正确的 FFmpeg 调色板命令。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            convert_mov_to_gif(
                input_path=Path("/tmp/test.mov"),
                output_path=Path("/tmp/test.gif"),
            )

        mock_run.assert_called_once()
        # 取出实际传递的命令列表（run 的第一个位置参数是一个 list）
        call_args = mock_run.call_args[0][0]

        assert call_args[0] == "ffmpeg"  # 或 ffmpeg 全路径
        assert "-i" in call_args
        assert str(Path("/tmp/test.mov")) in call_args
        assert str(Path("/tmp/test.gif")) in call_args
        # 验证调色板滤镜链中的关键片断
        filter_str = call_args[call_args.index("-vf") + 1]
        assert "fps=15" in filter_str
        assert "scale='min(480,iw)':'min(480,ih)'" in filter_str
        assert "palettegen" in filter_str
        assert "paletteuse" in filter_str
        assert "-loop" in call_args
        loop_idx = call_args.index("-loop") + 1
        assert call_args[loop_idx] == "0"  # 无限循环

    def test_ffmpeg_command_custom_params(self) -> None:
        """自定义 fps / max_size / loop=False 应体现在命令中。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            convert_mov_to_gif(
                input_path=Path("/tmp/video.mov"),
                output_path=Path("/tmp/out.gif"),
                fps=10,
                max_size=320,
                loop=False,
            )

        call_args = mock_run.call_args[0][0]
        filter_str = call_args[call_args.index("-vf") + 1]
        assert "fps=10" in filter_str
        assert "scale='min(320,iw)':'min(320,ih)'" in filter_str
        loop_idx = call_args.index("-loop") + 1
        assert call_args[loop_idx] == "1"  # 不循环

    def test_max_colors_added_to_palettegen(self) -> None:
        """max_colors 参数应出现在 palettegen 滤镜中（FFmpeg 7.0+ 兼容）。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            convert_mov_to_gif(
                input_path=Path("/tmp/v.mov"),
                output_path=Path("/tmp/v.gif"),
                max_colors=128,
            )

        call_args = mock_run.call_args[0][0]
        filter_str = call_args[call_args.index("-vf") + 1]
        assert "palettegen=max_colors=128" in filter_str

    def test_max_colors_omitted_when_default(self) -> None:
        """不传 max_colors 时 paletteuse 不应包含 max_colors 选项。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            convert_mov_to_gif(
                input_path=Path("/tmp/v.mov"),
                output_path=Path("/tmp/v.gif"),
            )

        call_args = mock_run.call_args[0][0]
        filter_str = call_args[call_args.index("-vf") + 1]
        assert "max_colors" not in filter_str

    def test_ffmpeg_path_resolved_via_shutil_which(self) -> None:
        """应通过 shutil.which 查找 ffmpeg，而非硬编码路径。"""
        with patch("src.converter.shutil.which") as mock_which, \
             patch("src.converter.subprocess.run"), \
             _RESOLVE:
            mock_which.return_value = "/usr/local/bin/ffmpeg"
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"))

        mock_which.assert_called_once_with("ffmpeg")

    # ── 错误处理测试 ────────────────────────────────────────────

    def test_raises_conversion_error_on_ffmpeg_failure(self) -> None:
        """FFmpeg 失败时应抛出 ConversionError 并包含 stderr。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            error = subprocess.CalledProcessError(
                returncode=1,
                cmd=["ffmpeg"],
                stderr=b"No such file or directory\n",
            )
            mock_run.side_effect = error

            with pytest.raises(ConversionError) as exc_info:
                convert_mov_to_gif(Path("/bad.mov"), Path("/out.gif"))

        assert "No such file or directory" in str(exc_info.value)
        # 原始异常链应保留
        assert exc_info.value.__cause__ is error

    def test_raises_conversion_error_when_ffmpeg_not_found(self) -> None:
        """未找到 FFmpeg 时应抛出 ConversionError。"""
        with patch("src.converter.shutil.which") as mock_which, \
             _RESOLVE:
            mock_which.return_value = None
            with pytest.raises(ConversionError) as exc_info:
                convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"))

        assert "FFmpeg" in str(exc_info.value)

    def test_raises_conversion_error_on_timeout(self) -> None:
        """FFmpeg 超时时应抛出 ConversionError，包含超时秒数。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            error = subprocess.TimeoutExpired(
                cmd=["ffmpeg"], timeout=300,
                stderr=b"process timed out\n",
            )
            mock_run.side_effect = error

            with pytest.raises(ConversionError) as exc_info:
                convert_mov_to_gif(Path("/big.mov"), Path("/out.gif"))

        assert "超时" in str(exc_info.value)
        assert "300" in str(exc_info.value)
        assert exc_info.value.__cause__ is error

    def test_raises_conversion_error_on_os_error(self) -> None:
        """FFmpeg 执行失败（如 FileNotFoundError）时应抛出 ConversionError。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run") as mock_run, \
             _RESOLVE:
            error = FileNotFoundError(2, "No such file", "ffmpeg")
            mock_run.side_effect = error

            with pytest.raises(ConversionError) as exc_info:
                convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"))

        assert "FFmpeg" in str(exc_info.value)
        assert exc_info.value.__cause__ is error

    # ── 参数验证测试 ────────────────────────────────────────────

    def test_raises_value_error_for_invalid_fps(self) -> None:
        """fps 超出 1-60 范围应抛出 ValueError。"""
        with pytest.raises(ValueError, match="帧率"):
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"), fps=0)
        with pytest.raises(ValueError, match="帧率"):
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"), fps=61)

    def test_raises_value_error_for_invalid_max_size(self) -> None:
        """max_size 超出 1-4096 范围应抛出 ValueError。"""
        with pytest.raises(ValueError, match="最大边长"):
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"), max_size=0)
        with pytest.raises(ValueError, match="最大边长"):
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"), max_size=4097)

    def test_raises_value_error_for_invalid_max_colors(self) -> None:
        """max_colors 超出 2-256 范围应抛出 ValueError。"""
        with pytest.raises(ValueError, match="最大颜色数"):
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"), max_colors=1)
        with pytest.raises(ValueError, match="最大颜色数"):
            convert_mov_to_gif(Path("/t.mov"), Path("/t.gif"), max_colors=257)

    # ── 路径类型测试 ────────────────────────────────────────────

    def test_accepts_string_paths(self) -> None:
        """应同时接受 str 和 Path 类型的路径参数。"""
        with patch("src.converter.shutil.which", return_value="ffmpeg"), \
             patch("src.converter.subprocess.run"), \
             _RESOLVE:
            # 不应抛出异常
            convert_mov_to_gif("/tmp/v.mov", "/tmp/o.gif")


class TestConversionError:
    """ConversionError 自定义异常测试。"""

    def test_is_exception_subclass(self) -> None:
        """应是 Exception 的子类。"""
        assert issubclass(ConversionError, Exception)

    def test_message_preserved(self) -> None:
        """错误消息应正确保存并展示。"""
        err = ConversionError("文件转换失败")
        assert str(err) == "文件转换失败"


# ── FFmpeg 集成测试 ──────────────────────────────────────────────────
# 以下测试需要系统安装 FFmpeg，否则在收集阶段自动跳过。
# 使用 ``@pytest.mark.ffmpeg`` 标记 + conftest.py 钩子实现。


@pytest.mark.ffmpeg
class TestConvertMovToGifIntegration:
    """convert_mov_to_gif 端到端集成测试 — 使用真实 FFmpeg 转换。

    所有测试依赖 conftest.py 中生成的 test_mov 夹具（64×64, 0.5s, 10fps）。
    在无 FFmpeg 环境中，整个类通过 pytest_collection_modifyitems 钩子自动跳过。
    """

    def test_converts_real_mov_to_gif(
        self, test_mov: Path, tmp_path: Path,
    ) -> None:
        """使用真实 FFmpeg 将测试 MOV 转换为 GIF，验证输出存在且非空。"""
        output = tmp_path / "output.gif"

        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output,
            fps=10,
            max_size=64,
        )

        assert output.exists(), "输出 GIF 文件应存在"
        assert output.stat().st_size > 0, "输出 GIF 不应为空"

    def test_output_gif_dimensions_within_max_size(
        self, test_mov: Path, tmp_path: Path, ffmpeg_path: str,
    ) -> None:
        """验证输出 GIF 尺寸不超过 max_size 限制（等比缩放）。"""
        output = tmp_path / "sized.gif"

        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output,
            max_size=32,  # 源视频 64×64 → 应缩放到 ≤32
        )

        # 使用 ffprobe（与 FFmpeg 同目录）获取 GIF 实际尺寸
        ffprobe = Path(ffmpeg_path).with_name(
            "ffprobe.exe" if Path(ffmpeg_path).suffix == ".exe" else "ffprobe"
        )
        result = subprocess.run(
            [
                str(ffprobe),
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                str(output),
            ],
            capture_output=True, text=True, check=True,
        )
        width_str, height_str = result.stdout.strip().split(",")
        width, height = int(width_str), int(height_str)

        assert width <= 32, f"宽度 {width} 应 ≤ max_size 32"
        assert height <= 32, f"高度 {height} 应 ≤ max_size 32"

    def test_conversion_error_on_corrupt_input(
        self, test_corrupt_mov: Path, tmp_path: Path,
    ) -> None:
        """损坏的/无效视频文件作为输入时应抛出 ConversionError。"""
        output = tmp_path / "fail.gif"

        with pytest.raises(ConversionError):
            convert_mov_to_gif(
                input_path=test_corrupt_mov,
                output_path=output,
            )

    def test_fps_parameter_controls_frame_rate(
        self, test_mov: Path, tmp_path: Path, ffmpeg_path: str,
    ) -> None:
        """自定义 fps 参数应影响输出 GIF 帧率。"""
        output = tmp_path / "fps_test.gif"

        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output,
            fps=5,
            max_size=64,
        )

        # 验证 ffprobe 可读取视频流信息（证明转换成功）
        ffprobe = Path(ffmpeg_path).with_name(
            "ffprobe.exe" if Path(ffmpeg_path).suffix == ".exe" else "ffprobe"
        )
        result = subprocess.run(
            [
                str(ffprobe),
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "csv=p=0",
                str(output),
            ],
            capture_output=True, text=True, check=True,
        )
        # r_frame_rate 返回如 "5/1" 格式
        assert "5" in result.stdout, f"帧率应包含 5，实际: {result.stdout}"

    def test_loop_parameter_controls_infinite_loop(
        self, test_mov: Path, tmp_path: Path,
    ) -> None:
        """loop=True 产生无限循环 GIF，loop=False 产生单次播放 GIF。

        不验证 GIF 内部元数据（需要专用解析库），只验证两种模式都成功转换。
        """
        output_loop = tmp_path / "loop_infinite.gif"
        output_noloop = tmp_path / "loop_once.gif"

        # 无限循环
        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output_loop,
            loop=True,
        )
        # 单次播放
        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output_noloop,
            loop=False,
        )

        assert output_loop.exists() and output_loop.stat().st_size > 0
        assert output_noloop.exists() and output_noloop.stat().st_size > 0
        # 两种模式的输出大小可能略有不同（loop 元数据差异）
        # 但都应该是有效的 GIF 文件

    def test_max_colors_limits_palette(
        self, test_mov: Path, tmp_path: Path,
    ) -> None:
        """max_colors 参数应能正常传递并完成转换。"""
        output_low = tmp_path / "low_colors.gif"
        output_high = tmp_path / "high_colors.gif"

        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output_low,
            max_colors=32,
        )
        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output_high,
            max_colors=256,
        )

        assert output_low.exists() and output_low.stat().st_size > 0
        assert output_high.exists() and output_high.stat().st_size > 0
        # 32 色调色板通常产生更小的文件
        assert output_low.stat().st_size <= output_high.stat().st_size, (
            f"32 色 ({output_low.stat().st_size} bytes) 应 ≤ "
            f"256 色 ({output_high.stat().st_size} bytes)"
        )

    def test_output_is_valid_gif(
        self, test_mov: Path, tmp_path: Path,
    ) -> None:
        """输出文件应是有效的 GIF 格式（以 GIF89a/GIF87a 魔术字节开头）。"""
        output = tmp_path / "valid.gif"

        convert_mov_to_gif(
            input_path=test_mov,
            output_path=output,
        )

        header = output.read_bytes()[:6]
        assert header[:3] == b"GIF", f"GIF 魔术字节应为 GIF，实际: {header[:3]}"
        assert header[3:6] in (b"89a", b"87a"), (
            f"GIF 版本应为 89a 或 87a，实际: {header[3:6]}"
        )

    def test_conversion_with_heic_input_uses_resolved_mov(
        self, test_mov: Path, tmp_path: Path,
    ) -> None:
        """通过 .heic 输入应能完成转换（resolve_input 自动映射到 .mov）。"""
        # 创建同名的 .heic 文件（空文件即可，resolve_input 会被真实调用）
        heic = test_mov.with_suffix(".heic")
        heic.touch()

        output = tmp_path / "from_heic.gif"

        convert_mov_to_gif(
            input_path=heic,
            output_path=output,
        )

        assert output.exists() and output.stat().st_size > 0
