"""CLI 模块的单元测试。

严格遵循 TDD：每个测试先于实现代码编写。
"""

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from src.cli import build_parser, parse_quality, collect_files, main


# ── 参数解析器测试 ────────────────────────────────────────────────

class TestBuildParser:
    """argparse 解析器结构测试。"""

    def setup_method(self) -> None:
        self.parser = build_parser()

    # 必选参数
    def test_input_positional_required(self) -> None:
        """input 是必选位置参数。"""
        with pytest.raises(SystemExit):
            self.parser.parse_args([])

    def test_input_positional_parsed(self) -> None:
        """input 位置参数应被正确解析。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.input == Path("test.mov")

    # 可选参数
    def test_output_defaults_to_none(self) -> None:
        """--output / -o 默认为 None。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.output is None

    def test_output_custom(self) -> None:
        """--output 可指定输出目录。"""
        args = self.parser.parse_args(["test.mov", "-o", "/out"])
        assert args.output == Path("/out")

    def test_frame_rate_default(self) -> None:
        """--frame-rate / -r 默认为 15。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.frame_rate == 15

    def test_frame_rate_custom(self) -> None:
        """--frame-rate 自定义值。"""
        args = self.parser.parse_args(["test.mov", "-r", "10"])
        assert args.frame_rate == 10

    def test_max_size_default(self) -> None:
        """--max-size / -s 默认为 480。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.max_size == 480

    def test_no_loop_flag(self) -> None:
        """--no-loop 为布尔开关，默认 False。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.no_loop is False

        args = self.parser.parse_args(["test.mov", "--no-loop"])
        assert args.no_loop is True

    def test_recursive_flag(self) -> None:
        """--recursive 为布尔开关，默认 False。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.recursive is False

        args = self.parser.parse_args(["test.mov", "--recursive"])
        assert args.recursive is True

    def test_quality_default(self) -> None:
        """--quality 默认为 None（不设 max_colors）。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.quality is None

    def test_quality_valid_choices(self) -> None:
        """--quality 接受 low/medium/high。"""
        for q in ("low", "medium", "high"):
            args = self.parser.parse_args(["test.mov", "--quality", q])
            assert args.quality == q

    def test_quality_invalid_choice(self) -> None:
        """--quality 非法值时退出。"""
        with pytest.raises(SystemExit):
            self.parser.parse_args(["test.mov", "--quality", "extreme"])

    def test_verbose_flag(self) -> None:
        """--verbose 为布尔开关。"""
        args = self.parser.parse_args(["test.mov"])
        assert args.verbose is False

        args = self.parser.parse_args(["test.mov", "--verbose"])
        assert args.verbose is True


# ── 质量映射测试 ──────────────────────────────────────────────────

class TestParseQuality:
    """质量预设映射测试。"""

    def test_low_maps_to_64(self) -> None:
        """low → max_colors=64。"""
        assert parse_quality("low") == 64

    def test_medium_maps_to_128(self) -> None:
        """medium → max_colors=128。"""
        assert parse_quality("medium") == 128

    def test_high_maps_to_256(self) -> None:
        """high → max_colors=256。"""
        assert parse_quality("high") == 256

    def test_none_returns_none(self) -> None:
        """None 输入返回 None。"""
        assert parse_quality(None) is None

    def test_invalid_quality_raises(self) -> None:
        """非法质量字符串抛出 ValueError。"""
        with pytest.raises(ValueError, match="无效的质量等级"):
            parse_quality("ultra")


# ── 文件收集测试 ──────────────────────────────────────────────────

class TestCollectFiles:
    """文件收集逻辑测试，使用 tmp_path 真实文件系统。"""

    def test_collects_heic_with_matching_mov(self, tmp_path: Path) -> None:
        """只收集有同名 .mov 的 .heic 文件对（返回 .heic 路径）。"""
        (tmp_path / "A.mov").touch()
        (tmp_path / "A.heic").touch()
        (tmp_path / "B.heic").touch()  # 无匹配 .mov
        (tmp_path / "B.mov").touch()
        (tmp_path / "notes.txt").touch()

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 2
        assert {f.name for f in files} == {"A.heic", "B.heic"}

    def test_collects_mov_files(self, tmp_path: Path) -> None:
        """也收集 .mov 文件（可直接转换）。"""
        (tmp_path / "video.mov").touch()
        (tmp_path / "photo.heic").touch()  # 无 .mov 匹配

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 1
        assert files[0].name == "video.mov"

    def test_recursive_collection(self, tmp_path: Path) -> None:
        """--recursive 递归子目录。"""
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "A.mov").touch()
        (tmp_path / "A.heic").touch()
        (sub / "B.mov").touch()
        (sub / "B.heic").touch()

        files = collect_files(tmp_path, recursive=True)

        assert len(files) == 2  # A 和 B 各一对

    def test_non_recursive_skips_subdirs(self, tmp_path: Path) -> None:
        """非递归模式只扫描顶层。"""
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "top.mov").touch()
        (tmp_path / "top.heic").touch()
        (sub / "deep.mov").touch()
        (sub / "deep.heic").touch()

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 1
        assert files[0].name == "top.heic"

    def test_empty_directory(self, tmp_path: Path) -> None:
        """空目录返回空列表。"""
        assert collect_files(tmp_path, recursive=False) == []

    def test_skips_hidden_files(self, tmp_path: Path) -> None:
        """跳过 . 开头隐藏文件。"""
        (tmp_path / ".hidden.mov").touch()
        (tmp_path / ".hidden.heic").touch()

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 0

    def test_mov_without_heic_is_collected(self, tmp_path: Path) -> None:
        """仅有 .mov（无对应 .heic）的文件应被独立收集。"""
        (tmp_path / "solo.mov").touch()

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 1
        assert files[0].name == "solo.mov"

    def test_multiple_pairs_sorted(self, tmp_path: Path) -> None:
        """多对文件应按名称排序返回。"""
        for name in ("C", "A", "B"):
            (tmp_path / f"{name}.mov").touch()
            (tmp_path / f"{name}.heic").touch()

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 3
        # 按 stem 排序
        assert [f.stem for f in files] == ["A", "B", "C"]

    def test_case_insensitive_extension(self, tmp_path: Path) -> None:
        """扩展名大小写不敏感。"""
        (tmp_path / "VIDEO.MOV").touch()
        (tmp_path / "VIDEO.HEIC").touch()

        files = collect_files(tmp_path, recursive=False)

        assert len(files) == 1
        assert files[0].suffix.lower() == ".heic"

    def test_heic_preferred_over_mov_for_same_stem(self, tmp_path: Path) -> None:
        """同时有 .heic 和 .mov 时优先收集 .heic（代表 Live Photo 对）。"""
        (tmp_path / "photo.mov").touch()
        (tmp_path / "photo.heic").touch()

        files = collect_files(tmp_path, recursive=False)

        # 应只返回 .heic（一个文件对只计一次）
        assert len(files) == 1
        assert files[0].suffix == ".heic"


# ── CLI 主流程测试 ────────────────────────────────────────────────

class TestMain:
    """main() 端到端集成测试（mock converter）。"""

    @pytest.fixture
    def mock_converter(self) -> MagicMock:
        with patch("src.cli.convert_mov_to_gif") as m:
            yield m

    @pytest.fixture
    def mock_resolver(self) -> MagicMock:
        with patch("src.cli.resolve_input", side_effect=lambda p: str(Path(p))) as m:
            yield m

    def test_single_file_conversion(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """单文件输入时应调用一次转换。"""
        mov = tmp_path / "test.mov"
        mov.touch()

        ret = main(["test.mov"], base_dir=str(tmp_path))

        assert ret == 0
        mock_converter.assert_called_once()

    def test_directory_batch(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """目录输入时应批量转换多个文件。"""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        for name in ("IMG_1", "IMG_2"):
            (photos_dir / f"{name}.mov").touch()
            (photos_dir / f"{name}.heic").touch()

        ret = main(["photos"], base_dir=str(tmp_path))

        assert ret == 0
        # 每个文件对调用一次
        assert mock_converter.call_count == 2

    def test_returns_1_on_input_error(
        self, mock_converter: MagicMock, tmp_path: Path
    ) -> None:
        """输入无法解析时返回退出码 1。"""
        ret = main(["nonexistent.mov"], base_dir=str(tmp_path))

        assert ret == 1
        mock_converter.assert_not_called()

    def test_default_output_dir_for_directory(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """目录模式默认输出到 input/output_gifs。"""
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        (photos_dir / "X.mov").touch()
        (photos_dir / "X.heic").touch()

        main(["photos"], base_dir=str(tmp_path), output_override=None)

        # 验证创建了 output_gifs 子目录
        expected_out = photos_dir / "output_gifs"
        assert expected_out.exists()

    def test_passes_quality_to_converter(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """--quality medium 应将 max_colors=128 传给转换函数。"""
        (tmp_path / "x.mov").touch()

        main(["x.mov", "--quality", "medium"], base_dir=str(tmp_path))

        call_kwargs = mock_converter.call_args.kwargs
        assert call_kwargs.get("max_colors") == 128

    def test_passes_no_loop_to_converter(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """--no-loop 应将 loop=False 传给转换函数。"""
        (tmp_path / "x.mov").touch()

        main(["x.mov", "--no-loop"], base_dir=str(tmp_path))

        call_kwargs = mock_converter.call_args.kwargs
        assert call_kwargs.get("loop") is False

    def test_passes_fps_and_size(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """自定义 -r 和 -s 应正确传递。"""
        (tmp_path / "x.mov").touch()

        main(["x.mov", "-r", "24", "-s", "720"], base_dir=str(tmp_path))

        call_kwargs = mock_converter.call_args.kwargs
        assert call_kwargs.get("fps") == 24
        assert call_kwargs.get("max_size") == 720

    def test_single_file_custom_output_dir(
        self, mock_converter: MagicMock, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """单文件模式指定 -o 输出目录应创建并使用。"""
        (tmp_path / "x.mov").touch()
        out_dir = tmp_path / "custom_out"

        main(["x.mov", "-o", "custom_out"], base_dir=str(tmp_path))

        assert out_dir.exists()
        # 验证转换被调用，输出路径在 custom_out 下
        call_args = mock_converter.call_args
        # convert_mov_to_gif 的参数都是 keyword 形式
        output_path = call_args.kwargs["output_path"]
        assert "custom_out" in str(output_path)

    def test_directory_with_no_valid_files_returns_0(
        self, mock_converter: MagicMock, tmp_path: Path
    ) -> None:
        """目录中无可转换文件时返回退出码 0（非错误）。"""
        photos_dir = tmp_path / "empty_photos"
        photos_dir.mkdir()
        (photos_dir / "notes.txt").touch()
        (photos_dir / "readme.md").touch()

        ret = main(["empty_photos"], base_dir=str(tmp_path))

        assert ret == 0
        mock_converter.assert_not_called()

    def test_non_existent_path_type_returns_1(
        self, mock_converter: MagicMock, tmp_path: Path
    ) -> None:
        """输入路径既非文件也非目录时返回退出码 1。"""
        # 创建一个路径字符串，它对应的文件/目录不存在
        ret = main(["ghost_path"], base_dir=str(tmp_path))

        assert ret == 1
        mock_converter.assert_not_called()

    def test_verbose_flag_output(
        self, mock_converter: MagicMock, mock_resolver: MagicMock,
        tmp_path: Path, capsys: pytest.CaptureFixture,
    ) -> None:
        """--verbose 应打印详细转换日志。"""
        (tmp_path / "v.mov").touch()

        main(["v.mov", "--verbose"], base_dir=str(tmp_path))

        captured = capsys.readouterr()
        assert "输入" in captured.out or "输出" in captured.out or "参数" in captured.out

    def test_returns_1_on_single_conversion_error(
        self, mock_resolver: MagicMock, tmp_path: Path
    ) -> None:
        """单文件转换失败（ConversionError）时返回退出码 1。"""
        from src.converter import ConversionError

        (tmp_path / "bad.mov").touch()

        with patch("src.cli.convert_mov_to_gif",
                   side_effect=ConversionError("FFmpeg 崩溃")):
            ret = main(["bad.mov"], base_dir=str(tmp_path))

        assert ret == 1
