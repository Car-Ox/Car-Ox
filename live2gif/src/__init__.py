"""LiveToGif — 将 Apple Live Photo 转换为高质量 GIF 动图。

主要 API:
    from src import convert_mov_to_gif, resolve_input, main
    from src import LiveToGifGUI  # GUI
"""

from src.cli import main
from src.converter import ConversionError, convert_mov_to_gif
from src.gui import LiveToGifGUI
from src.input_resolver import InputError, resolve_input

__all__ = [
    "convert_mov_to_gif",
    "ConversionError",
    "resolve_input",
    "InputError",
    "main",
    "LiveToGifGUI",
]
