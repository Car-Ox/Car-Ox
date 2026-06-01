"""pytest 全局配置与共享夹具。

提供:
- FFmpeg 可用性检测（shutil.which）
- 自定义 pytest 标记注册
- 测试视频生成（通过 FFmpeg lavfi）
- 跨模块复用的夹具
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


# ── FFmpeg 可用性检测 ────────────────────────────────────────────────

def ffmpeg_available() -> bool:
    """检测系统是否安装了 FFmpeg 并可通过 PATH 访问。"""
    return shutil.which("ffmpeg") is not None


# ── pytest 配置钩子 ──────────────────────────────────────────────────

def pytest_configure(config: pytest.Config) -> None:
    """注册自定义 pytest 标记，消除 PytestUnknownMarkWarning。"""
    config.addinivalue_line(
        "markers",
        "ffmpeg: 需要系统安装 FFmpeg 的集成测试（无 FFmpeg 时自动跳过）。",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item],
) -> None:
    """标记为 ``ffmpeg`` 的测试在无 FFmpeg 环境自动跳过。

    该钩子在测试收集完成后、执行前运行，为每个标记了 ffmpeg
    的测试项动态添加 ``pytest.mark.skip``。
    """
    if ffmpeg_available():
        return  # FFmpeg 可用，不跳过任何测试

    skip_ffmpeg = pytest.mark.skip(reason="FFmpeg 未安装或不在 PATH 中")
    for item in items:
        if "ffmpeg" in item.keywords:
            item.add_marker(skip_ffmpeg)


# ── 共享夹具 ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def ffmpeg_path() -> str:
    """返回 FFmpeg 可执行文件的完整路径（session 级别缓存）。

    仅在 FFmpeg 可用时被调用；不可用时由 ffmpeg 标记的
    skipif 机制在收集阶段跳过。
    """
    path = shutil.which("ffmpeg")
    if path is None:
        pytest.skip("FFmpeg 未安装或不在 PATH 中")
    return path


@pytest.fixture(scope="module")
def test_media_dir(ffmpeg_path: str, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """为集成测试创建媒体文件临时目录（模块级别复用）。

    该夹具依赖 ffmpeg_path，确保只在 FFmpeg 可用时创建。
    """
    return tmp_path_factory.mktemp("test_media")


@pytest.fixture(scope="module")
def test_mov(ffmpeg_path: str, test_media_dir: Path) -> Path:
    """使用 FFmpeg 生成微小的测试 MOV 视频文件。

    规格:
    - 分辨率: 64×64 像素
    - 时长: 0.5 秒
    - 帧率: 10 fps
    - 编码: H.264 (libx264) + YUV420P

    模块级别作用域，同一模块内的所有集成测试复用同一个文件，
    避免重复编码。
    """
    output = test_media_dir / "test_video.mov"
    cmd = [
        ffmpeg_path,
        "-f", "lavfi",
        "-i", "testsrc=duration=0.5:size=64x64:rate=10",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-y",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return output


@pytest.fixture(scope="module")
def test_corrupt_mov(test_media_dir: Path) -> Path:
    """生成伪装为 .mov 的文本文件（模拟损坏/无效视频）。"""
    output = test_media_dir / "corrupt.mov"
    output.write_text("this is not a valid mov file\n" * 10)
    return output
