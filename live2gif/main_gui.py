"""LiveToGif GUI 启动入口。

用法:
    python main_gui.py

启动图形用户界面，支持拖拽或选择 Live Photo 文件进行转换。
打包为 macOS .app 后双击即可使用。
"""

from src.gui import LiveToGifGUI


def main() -> None:
    """启动 GUI 应用。"""
    app = LiveToGifGUI()
    app.run()


if __name__ == "__main__":
    main()
