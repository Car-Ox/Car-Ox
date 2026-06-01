"""LiveToGif 项目入口。

用法:
    python main.py IMG_1234.heic
    python main.py ./Photos --recursive --quality high
    python main.py IMG_1234.mov -r 24 -s 720 --no-loop --verbose

也可直接:
    python -m live2gif IMG_1234.heic
"""

from src.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
