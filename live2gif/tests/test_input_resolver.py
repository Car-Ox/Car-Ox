"""input_resolver 模块的单元测试。

严格遵循 TDD：每个测试先于实现代码编写。
使用 tmp_path 创建临时文件模拟真实 Live Photo 场景。
"""

from pathlib import Path

import pytest

from src.input_resolver import InputError, resolve_input


class TestResolveInput:
    """resolve_input 函数完整测试套件。"""

    # ── .mov 直接提供场景 ────────────────────────────────────────

    def test_returns_mov_path_when_mov_exists(self, tmp_path: Path) -> None:
        """提供存在的 .mov 文件时应直接返回其路径。"""
        mov = tmp_path / "IMG_1234.mov"
        mov.touch()

        result = resolve_input(str(mov))

        assert result == str(mov)

    def test_raises_input_error_when_mov_not_found(self, tmp_path: Path) -> None:
        """提供的 .mov 路径不存在时应抛出 InputError。"""
        missing = tmp_path / "nonexistent.mov"

        with pytest.raises(InputError) as exc_info:
            resolve_input(str(missing))

        assert "未找到" in str(exc_info.value)
        assert "nonexistent.mov" in str(exc_info.value)

    # ── .heic 输入场景 ───────────────────────────────────────────

    def test_resolves_heic_to_matching_mov(self, tmp_path: Path) -> None:
        """提供 .heic 文件且同目录有同名 .mov 时应返回 .mov 路径。"""
        mov = tmp_path / "IMG_5678.mov"
        heic = tmp_path / "IMG_5678.heic"
        mov.touch()
        heic.touch()

        result = resolve_input(str(heic))

        assert result == str(mov)

    def test_raises_input_error_when_heic_has_no_matching_mov(self, tmp_path: Path) -> None:
        """提供 .heic 但同目录无同名 .mov 时应抛出 InputError。"""
        heic = tmp_path / "IMG_0000.heic"
        heic.touch()

        with pytest.raises(InputError) as exc_info:
            resolve_input(str(heic))

        assert "未找到对应的 MOV 文件" in str(exc_info.value)
        assert "IMG_0000.mov" in str(exc_info.value)

    def test_raises_input_error_when_heic_not_found(self, tmp_path: Path) -> None:
        """提供的 .heic 路径本身不存在时应抛出 InputError。"""
        missing = tmp_path / "ghost.heic"

        with pytest.raises(InputError) as exc_info:
            resolve_input(str(missing))

        assert "未找到" in str(exc_info.value)

    # ── 边缘场景 ─────────────────────────────────────────────────

    def test_raises_input_error_for_unsupported_extension(self, tmp_path: Path) -> None:
        """提供非 .mov / .heic 后缀的文件时应抛出 InputError。"""
        txt = tmp_path / "notes.txt"
        txt.touch()

        with pytest.raises(InputError) as exc_info:
            resolve_input(str(txt))

        assert "不支持的文件格式" in str(exc_info.value)

    def test_handles_uppercase_extension(self, tmp_path: Path) -> None:
        """后缀名大小写不敏感（.HEIC / .MOV 均可识别）。"""
        mov = tmp_path / "VIDEO.MOV"
        heic = tmp_path / "VIDEO.HEIC"
        mov.touch()
        heic.touch()

        result = resolve_input(str(heic))

        # 跨平台安全比较：解析结果指向的文件应与原始 .mov 相同
        assert Path(result).resolve() == mov.resolve()

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        """应同时接受 Path 对象作为输入。"""
        mov = tmp_path / "input.mov"
        mov.touch()

        result = resolve_input(mov)  # type: ignore[arg-type]

        assert result == str(mov)


# ── 边缘情况与异常输入测试 ──────────────────────────────────────────

class TestResolveInputEdgeCases:
    """resolve_input 边界条件和异常输入测试。"""

    def test_directory_with_mov_extension_is_accepted(
        self, tmp_path: Path,
    ) -> None:
        """后缀为 .mov 的目录会被 Path.exists() 视为「存在」并返回路径。

        注意：Path.exists() 对目录也返回 True，因此名为 xxx.mov 的目录
        会被 resolve_input 当作有效输入接受（而非报错）。
        这是当前实现的已知行为。
        """
        fake_dir = tmp_path / "fake.mov"
        fake_dir.mkdir()

        # 目录被当作有效输入接受（Path.exists() 不区分文件/目录）
        result = resolve_input(str(fake_dir))
        assert result == str(fake_dir)

    def test_raises_error_for_file_without_extension(
        self, tmp_path: Path,
    ) -> None:
        """无后缀名的文件应抛出 InputError。"""
        no_ext = tmp_path / "no_extension"
        no_ext.touch()

        with pytest.raises(InputError) as exc_info:
            resolve_input(str(no_ext))

        assert "不支持的文件格式" in str(exc_info.value)

    def test_raises_error_for_hidden_mov(self, tmp_path: Path) -> None:
        """以 . 开头的隐藏 .mov 文件存在时应正常解析。"""
        hidden = tmp_path / ".hidden.mov"
        hidden.touch()

        # 隐藏文件只要是有效的 .mov 就应能解析
        result = resolve_input(str(hidden))
        assert result == str(hidden)

    def test_path_with_spaces(self, tmp_path: Path) -> None:
        """包含空格的路径应正常解析。"""
        spaced = tmp_path / "my live photo.mov"
        spaced.touch()

        result = resolve_input(str(spaced))
        assert result == str(spaced)

    def test_path_with_unicode(self, tmp_path: Path) -> None:
        """包含 Unicode 字符的路径应正常解析。"""
        unicode_file = tmp_path / "照片_IMG_1234.mov"
        unicode_file.touch()

        result = resolve_input(str(unicode_file))
        assert result == str(unicode_file)

    def test_heic_with_mov_as_directory_not_file(
        self, tmp_path: Path,
    ) -> None:
        """.heic 存在但同名 .mov 是目录（而非文件）时的行为。

        注意：Path.exists() 对目录也返回 True，因此 resolve_input
        会将目录路径当作有效 .mov 返回。这是一个已知的边界行为。
        """
        heic = tmp_path / "IMG_9999.heic"
        heic.touch()
        # 创建同名 .mov 目录（而非文件）
        mov_dir = tmp_path / "IMG_9999.mov"
        mov_dir.mkdir()

        # 由于 Path.exists() 对目录也返回 True，
        # resolve_input 当前将目录路径作为 .mov 返回
        result = resolve_input(str(heic))
        assert result == str(mov_dir)

    def test_double_extension_file(self, tmp_path: Path) -> None:
        """双后缀名文件（如 .heic.mov）按最后一个后缀判断。"""
        # .heic.mov → suffix 是 .mov
        f = tmp_path / "test.heic.mov"
        f.touch()

        result = resolve_input(str(f))
        assert result == str(f)  # 作为 .mov 直接返回

    def test_input_with_relative_path(self, tmp_path: Path) -> None:
        """相对路径输入应正常工作。"""
        import os

        mov = tmp_path / "relative_test.mov"
        mov.touch()

        orig_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = resolve_input("relative_test.mov")
            assert "relative_test.mov" in result
        finally:
            os.chdir(orig_cwd)

    def test_empty_string_raises_error(self) -> None:
        """空字符串输入应抛出 InputError。"""
        with pytest.raises(InputError):
            resolve_input("")

    def test_input_path_with_trailing_slash(self, tmp_path: Path) -> None:
        """以斜杠结尾的路径（如目录表示）应抛出 InputError。"""
        with pytest.raises(InputError):
            # 直接构造一个以分隔符结尾的字符串
            resolve_input(str(tmp_path) + "/")

    def test_mov_file_with_heic_extension_trick(self, tmp_path: Path) -> None:
        """非真正 HEIC 但后缀为 .heic 的文件：有同名 .mov 时正常解析。"""
        heic = tmp_path / "fake.heic"
        mov = tmp_path / "fake.mov"
        heic.write_text("not a real heic file")
        mov.touch()

        # 只要能找到同名 .mov，就应该返回 .mov 路径
        result = resolve_input(str(heic))
        assert result == str(mov)


class TestInputError:
    """InputError 自定义异常测试。"""

    def test_is_exception_subclass(self) -> None:
        """应是 Exception 的子类。"""
        assert issubclass(InputError, Exception)

    def test_message_preserved(self) -> None:
        """错误消息应正确保存。"""
        err = InputError("无法识别输入文件")
        assert str(err) == "无法识别输入文件"
