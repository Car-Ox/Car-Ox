"""quality_presets 模块的单元测试。

测试 CLI 与 GUI 共享的质量预设映射和辅助函数。
"""


import pytest

from src.quality_presets import QUALITY_MAP, quality_to_max_colors


class TestQualityMap:
    """QUALITY_MAP 常量测试。"""

    def test_contains_low_medium_high(self) -> None:
        """应包含 low、medium、high 三个键。"""
        assert set(QUALITY_MAP.keys()) == {"low", "medium", "high"}

    def test_low_maps_to_64(self) -> None:
        """low 应对应 64 色。"""
        assert QUALITY_MAP["low"] == 64

    def test_medium_maps_to_128(self) -> None:
        """medium 应对应 128 色。"""
        assert QUALITY_MAP["medium"] == 128

    def test_high_maps_to_256(self) -> None:
        """high 应对应 256 色。"""
        assert QUALITY_MAP["high"] == 256


class TestQualityToMaxColors:
    """quality_to_max_colors 函数测试。"""

    def test_low_returns_64(self) -> None:
        """low 应返回 64。"""
        assert quality_to_max_colors("low") == 64

    def test_medium_returns_128(self) -> None:
        """medium 应返回 128。"""
        assert quality_to_max_colors("medium") == 128

    def test_high_returns_256(self) -> None:
        """high 应返回 256。"""
        assert quality_to_max_colors("high") == 256

    def test_none_returns_none(self) -> None:
        """None 输入应返回 None（使用默认值）。"""
        assert quality_to_max_colors(None) is None

    def test_invalid_quality_raises_value_error(self) -> None:
        """无效的质量等级应抛出 ValueError。"""
        with pytest.raises(ValueError) as exc_info:
            quality_to_max_colors("ultra")
        assert "ultra" in str(exc_info.value)
        assert "质量" in str(exc_info.value)
