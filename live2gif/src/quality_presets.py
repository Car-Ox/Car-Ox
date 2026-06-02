"""CLI 与 GUI 共享的质量预设常量与辅助函数。

提取自 cli.py 和 gui.py 中重复的质量映射逻辑，
避免 DRY 违规，确保两处行为一致。
"""

from __future__ import annotations

# 质量预设 → max_colors 映射
QUALITY_MAP: dict[str, int] = {
    "low": 64,
    "medium": 128,
    "high": 256,
}


def quality_to_max_colors(quality: str | None) -> int | None:
    """将质量字符串映射为 max_colors 数值。

    Args:
        quality: "low" / "medium" / "high" 或 None。

    Returns:
        max_colors 整数值，None 时返回 None。

    Raises:
        ValueError: 无效的质量等级。
    """
    if quality is None:
        return None
    if quality not in QUALITY_MAP:
        raise ValueError(
            f"无效的质量等级「{quality}」，可选：{', '.join(QUALITY_MAP)}"
        )
    return QUALITY_MAP[quality]
