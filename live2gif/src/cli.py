"""LiveToGif 命令行界面。

使用 argparse 实现完整的 CLI，支持单文件、文件夹批量、自定义参数。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.converter import ConversionError, convert_mov_to_gif
from src.input_resolver import InputError, resolve_input
from src.quality_presets import quality_to_max_colors

# 并行转换最大线程数（可通过 --workers 参数或 LIVE2GIF_MAX_WORKERS 环境变量覆盖）
_MAX_WORKERS_DEFAULT = int(os.environ.get("LIVE2GIF_MAX_WORKERS", "4"))


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。

    Returns:
        配置好的 ArgumentParser 实例。
    """
    parser = argparse.ArgumentParser(
        prog="live2gif",
        description="将 Apple Live Photo (.heic + .mov) 转换为高质量 GIF 动图。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  live2gif IMG_1234.heic                    # 单文件转换
  live2gif IMG_1234.heic -o ./output        # 指定输出目录
  live2gif ./Photos --recursive             # 递归批量转换
  live2gif IMG_1234.mov -r 24 -s 720        # 自定义帧率和尺寸
  live2gif IMG_1234.heic --quality high     # 高质量（256 色）
  live2gif IMG_1234.heic --no-loop --verbose # 不循环 + 详细日志
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="输入文件（.mov / .heic）或包含 Live Photo 的目录路径。",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="输出目录（默认：单文件与输入同目录，目录模式为 input/output_gifs）。",
    )

    parser.add_argument(
        "-r", "--frame-rate",
        type=int,
        default=15,
        metavar="FPS",
        help="输出 GIF 帧率（默认 15）。",
    )

    parser.add_argument(
        "-s", "--max-size",
        type=int,
        default=480,
        metavar="PX",
        help="输出 GIF 最大边长（像素），等比缩放（默认 480）。",
    )

    parser.add_argument(
        "--no-loop",
        action="store_true",
        default=False,
        help="禁用 GIF 无限循环（默认开启）。",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        default=False,
        help="目录模式下递归处理子文件夹。",
    )

    parser.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        default=None,
        help="输出质量预设：low（64 色）、medium（128 色）、high（256 色）。",
    )

    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=_MAX_WORKERS_DEFAULT,
        metavar="N",
        help=f"并行转换线程数（默认 {_MAX_WORKERS_DEFAULT}，可通过环境变量 "
             f"LIVE2GIF_MAX_WORKERS 设置）。",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="打印详细的转换日志。",
    )

    return parser


def collect_files(directory: Path, recursive: bool = False) -> list[Path]:
    """扫描目录，收集可转换的 Live Photo 文件。

    优先级：
    1. 有同名 .mov 的 .heic 文件（返回 .heic 路径，由 resolve_input 处理）
    2. 独立的 .mov 文件

    Args:
        directory: 目标目录路径。
        recursive: 是否递归子目录。

    Returns:
        可转换的文件路径列表（已排序）。
    """
    pattern = "**/*" if recursive else "*"
    all_files: list[Path] = []

    for f in directory.glob(pattern):
        if not f.is_file():
            continue
        if f.name.startswith("."):
            continue
        suffix = f.suffix.lower()
        if suffix in (".heic", ".mov"):
            all_files.append(f)

    # 构建 .mov 文件集合用于匹配
    mov_names: set[str] = set()
    for f in all_files:
        if f.suffix.lower() == ".mov":
            mov_names.add(f.stem)

    # 收集结果：优先 .heic（有匹配 .mov 的），然后 .mov
    result: list[Path] = []
    seen_stems: set[str] = set()
    heic_files: list[Path] = []

    for f in all_files:
        suffix = f.suffix.lower()
        if suffix == ".heic":
            if f.stem in mov_names:
                result.append(f)
                seen_stems.add(f.stem)
            else:
                heic_files.append(f)
        elif suffix == ".mov":
            if f.stem not in seen_stems:
                result.append(f)
                seen_stems.add(f.stem)

    result.sort()
    return result


def main(argv: Sequence[str] | None = None, *,
         base_dir: str | None = None,
         output_override: Path | None = None) -> int:
    """CLI 主入口。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv[1:]。
        base_dir: 测试时的工作目录覆盖（所有相对路径基于此目录）。
        output_override: 测试时的输出目录覆盖。

    Returns:
        退出码：0 成功，1 出错。
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # 测试辅助：切换到指定工作目录
    if base_dir:
        os.chdir(base_dir)

    input_path = args.input.resolve()

    # 确定输入类型
    if input_path.is_file():
        return _convert_single(
            input_path=input_path,
            output=output_override or args.output,
            fps=args.frame_rate,
            max_size=args.max_size,
            loop=not args.no_loop,
            max_colors=quality_to_max_colors(args.quality),
            verbose=args.verbose,
        )
    elif input_path.is_dir():
        return _convert_directory(
            directory=input_path,
            output=output_override or args.output,
            fps=args.frame_rate,
            max_size=args.max_size,
            loop=not args.no_loop,
            max_colors=quality_to_max_colors(args.quality),
            recursive=args.recursive,
            verbose=args.verbose,
            workers=args.workers,
        )
    else:
        print(f"❌ 输入路径不存在: {input_path}", file=sys.stderr)
        return 1


# ── 内部辅助函数 ────────────────────────────────────────────────────────────

def _convert_single(
    input_path: Path,
    output: Path | None,
    fps: int,
    max_size: int,
    loop: bool,
    max_colors: int | None,
    verbose: bool,
) -> int:
    """处理单文件转换。

    执行流程：输入解析 → 输出路径构造 → FFmpeg 转换 → 结果反馈。

    Args:
        input_path: 已解析为绝对路径的输入文件（.mov 或 .heic）。
        output: 输出目录，None 时使用输入文件所在目录。
        fps: GIF 帧率。
        max_size: GIF 最大边长（像素）。
        loop: 是否无限循环。
        max_colors: 调色板最大颜色数，None 使用默认。
        verbose: 是否打印详细日志。

    Returns:
        0 表示转换成功，1 表示失败。
    """
    try:
        resolved = resolve_input(str(input_path))
    except InputError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    if output is None:
        output = input_path.parent
    output.mkdir(parents=True, exist_ok=True)

    stem = Path(resolved).stem
    output_file = output / f"{stem}.gif"

    if verbose:
        print(f"📥 输入:  {input_path}")
        print(f"📤 输出:  {output_file}")
        print(f"⚙️  参数:  fps={fps}, size={max_size}, loop={loop}"
              f"{', max_colors=' + str(max_colors) if max_colors else ''}")
        print("🔄 转换中...")

    try:
        convert_mov_to_gif(
            input_path=input_path,
            output_path=output_file,
            fps=fps,
            max_size=max_size,
            loop=loop,
            max_colors=max_colors,
        )
    except (ConversionError, InputError) as e:
        print(f"❌ 转换失败: {e}", file=sys.stderr)
        return 1

    print(f"✅ 已生成: {output_file}")
    return 0


def _convert_directory(
    directory: Path,
    output: Path | None,
    fps: int,
    max_size: int,
    loop: bool,
    max_colors: int | None,
    recursive: bool,
    verbose: bool,
    workers: int = 4,
) -> int:
    """处理目录批量转换。

    扫描目录收集 Live Photo 文件，使用线程池并行转换，
    并提供进度反馈和最终统计。

    Ctrl+C 中断时会优雅退出，取消所有未开始的任务。

    Args:
        directory: 已解析为绝对路径的目标目录。
        output: 输出目录，None 时自动创建 output_gifs 子目录。
        fps: GIF 帧率。
        max_size: GIF 最大边长（像素）。
        loop: 是否无限循环。
        max_colors: 调色板最大颜色数，None 使用默认。
        recursive: 是否递归扫描子目录。
        verbose: 是否打印逐文件进度。
        workers: 并行转换线程数，默认 4。

    Returns:
        0 表示全部成功，1 表示有失败（或被用户中断）。
    """
    files = collect_files(directory, recursive=recursive)

    if not files:
        print(f"⚠️  在「{directory}」中未找到可转换的 Live Photo 文件。")
        return 0

    if output is None:
        output = directory / "output_gifs"
    output.mkdir(parents=True, exist_ok=True)

    total = len(files)
    print(f"📂 找到 {total} 个文件，输出到: {output}")

    success = 0
    failed = 0
    start_time = time.monotonic()

    def _convert_one(f: Path) -> tuple[Path, bool, str]:
        """单个文件转换任务（线程池调用）。"""
        try:
            resolved = resolve_input(str(f))
        except InputError as e:
            return (f, False, str(e))
        out = output / f"{Path(resolved).stem}.gif"
        try:
            convert_mov_to_gif(
                input_path=f,
                output_path=out,
                fps=fps,
                max_size=max_size,
                loop=loop,
                max_colors=max_colors,
            )
            return (f, True, str(out))
        except (ConversionError, InputError) as e:
            return (f, False, str(e))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_convert_one, f): f for f in files}

        try:
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    f, ok, msg = future.result()
                except KeyboardInterrupt:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise
                if ok:
                    success += 1
                    if verbose:
                        print(f"  [{i}/{total}] ✅ {f.name} → {msg}")
                else:
                    failed += 1
                    print(f"  [{i}/{total}] ❌ {f.name}: {msg}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n⚠️  用户中断，正在取消剩余任务...")
            failed += total - success - failed

    elapsed = time.monotonic() - start_time

    # 统计信息
    print(f"\n{'='*50}")
    print(f"  完成: {total} 个文件 | 成功: {success} | 失败: {failed}")
    print(f"  耗时: {elapsed:.1f} 秒")
    print(f"  输出: {output.resolve()}")
    print(f"{'='*50}")

    return 0 if failed == 0 else 1
