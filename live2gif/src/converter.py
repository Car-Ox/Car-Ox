"""Live Photo .MOV → GIF 转换模块。

使用 FFmpeg 高质量调色板模式将 MOV 视频转换为 GIF 动图。
支持直接传入 .heic 文件，自动解析为同名 .mov。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from src.input_resolver import resolve_input, InputError


class ConversionError(Exception):
    """FFmpeg 转换过程中发生的错误。

    Attributes:
        message: 人类可读的错误描述，包含 FFmpeg stderr 输出。
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


def _resolve_ffmpeg() -> str:
    """查找系统 FFmpeg 可执行文件路径。

    搜索优先级：
    1. PyInstaller 打包后的 bundle 内 FFmpeg（sys._MEIPASS/ffmpeg）
    2. 系统 PATH 中的 FFmpeg

    Returns:
        FFmpeg 的完整路径字符串。

    Raises:
        ConversionError: 系统中未找到 FFmpeg。
    """
    # 打包模式：优先使用 .app bundle 内的 FFmpeg 静态二进制
    if getattr(sys, 'frozen', False):
        meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        bundled = meipass / "ffmpeg"
        if bundled.exists():
            return str(bundled)

    # 开发模式：使用系统 PATH 中的 FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise ConversionError("未找到 FFmpeg，请确认已安装并添加到系统 PATH 中。")
    return ffmpeg_path


def convert_mov_to_gif(
    input_path: str | Path,
    output_path: str | Path,
    fps: int = 15,
    max_size: int = 480,
    loop: bool = True,
    max_colors: int | None = None,
) -> None:
    """将 Live Photo (.mov 或 .heic) 转换为高质量 GIF 动图。

    使用 FFmpeg 双通道调色板模式，在保证画质的同时控制文件体积。
    支持直接传入 .heic 文件，自动查找同目录同名 .mov 进行转换。

    Args:
        input_path: 输入文件路径（str 或 Path），支持 .mov 或 .heic。
        output_path: 输出 .gif 文件路径（str 或 Path）。
        fps: 输出 GIF 帧率，默认 15。
        max_size: 输出 GIF 最大宽/高（像素），等比缩放，默认 480。
        loop: True 表示无限循环（-loop 0），False 表示播放一次（-loop 1）。
        max_colors: 调色板最大颜色数，默认 None（FFmpeg 默认 256）。
            典型值：64（低质量）、128（中等）、256（高质量）。

    Raises:
        ConversionError: FFmpeg 未找到或转换过程出错。
        InputError: 输入文件无法解析（格式不支持、文件不存在等）。
    """
    # 解析输入：支持 .heic → .mov 自动映射
    resolved_mov = resolve_input(input_path)
    output_p = Path(output_path)

    ffmpeg = _resolve_ffmpeg()

    # 构建调色板滤镜链
    # 注意：FFmpeg 7.0+ 中 paletteuse 不再支持 max_colors 选项，
    # 需要将 max_colors 放在 palettegen 上。
    palettegen = "palettegen"
    if max_colors is not None:
        palettegen = f"palettegen=max_colors={max_colors}"

    vf_filter = (
        f"fps={fps},"
        f"scale='min({max_size},iw)':'min({max_size},ih)':force_original_aspect_ratio=decrease,"
        "split[a][b];"
        f"[a]{palettegen}[p];"
        "[b][p]paletteuse"
    )

    loop_value = "0" if loop else "1"

    cmd = [
        ffmpeg,
        "-i", resolved_mov,
        "-vf", vf_filter,
        "-loop", loop_value,
        str(output_p),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ConversionError(exc.stderr.strip()) from exc


# ── 测试块 ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Windows 上请将 TEST_INPUT 替换为实际存在的 Live Photo 文件路径
    # 支持 .mov 或 .heic（会自动查找同名 .mov）
    TEST_INPUT = r"D:\test_live_photo.mov"  # 或 .heic
    TEST_GIF = r"D:\test_output.gif"

    try:
        print(f"正在转换: {TEST_INPUT} → {TEST_GIF}")
        convert_mov_to_gif(TEST_INPUT, TEST_GIF, fps=15, max_size=480, loop=True)
        print(f"✅ 转换成功！输出文件: {TEST_GIF}")
    except (ConversionError, InputError) as e:
        print(f"❌ 转换失败: {e}")
