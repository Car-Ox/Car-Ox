"""Live Photo 输入解析模块。

自动识别用户输入，将 .heic 文件映射到同名 .mov 文件，
为后续 GIF 转换提供统一的 .mov 入口。
"""

from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".mov", ".heic"}


class InputError(Exception):
    """输入文件无法解析时抛出的异常。

    Attributes:
        message: 人类可读的错误描述。
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


def resolve_input(user_input: str | Path) -> str:
    """解析用户输入，返回可用的 .mov 文件路径。

    规则（按优先级）：
    1. 如果是 .mov 且存在 → 直接返回。
    2. 如果是 .heic 且存在 → 查找同目录同名 .mov → 返回 .mov 路径。
    3. 否则抛出 InputError。

    Args:
        user_input: 用户提供的文件路径（str 或 Path），支持 .mov 或 .heic。

    Returns:
        解析后的 .mov 文件路径字符串。

    Raises:
        InputError: 文件不存在、格式不支持、或找不到匹配的 .mov。
    """
    path = Path(user_input)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise InputError(
            f"不支持的文件格式「{path.suffix}」。"
            f"请提供 Live Photo 的 .mov 或 .heic 文件。"
        )

    if not path.exists():
        raise InputError(f"未找到文件: {path}")

    if suffix == ".mov":
        return str(path)

    # suffix == ".heic"：查找同名 .mov
    mov_path = path.with_suffix(".mov")
    if mov_path.exists():
        return str(mov_path)

    raise InputError(
        f"未找到对应的 MOV 文件「{mov_path.name}」。"
        f"请确认 .heic 和 .mov 文件在同一目录下且文件名一致。"
    )
