#!/usr/bin/env bash
# =============================================================================
# Live2Gif — macOS 本地构建脚本
# =============================================================================
# 用途：在本地 Mac 上构建 Live2Gif.app 并打包为 .dmg。
#
# 前置条件：
#   1. macOS 11.0+
#   2. Python 3.10+（推荐 3.11）
#   3. Homebrew 已安装（https://brew.sh）
#
# 用法：
#   chmod +x build_macos.sh
#   ./build_macos.sh
#
# 产物：
#   dist/Live2Gif.app     — 应用程序包
#   Live2Gif.dmg          — 安装镜像
# =============================================================================

set -euo pipefail

# ── 颜色输出 ────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 检测系统环境 ────────────────────────────────────────────────────────────
echo ""
echo "================================================"
echo "  Live2Gif macOS 构建脚本"
echo "================================================"
echo ""

# macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    error "此脚本仅在 macOS 上运行。请在 Mac 上使用。"
fi
info "系统: $(sw_vers -productName) $(sw_vers -productVersion)"

# Python
PYTHON="python3"
if ! command -v $PYTHON &>/dev/null; then
    error "未找到 python3，请先安装 Python 3.10+"
fi
PY_VER=$($PYTHON --version 2>&1 | awk '{print $2}')
info "Python: $PY_VER"

# Homebrew
if ! command -v brew &>/dev/null; then
    error "未找到 Homebrew，请先安装: https://brew.sh"
fi
info "Homebrew: $(brew --version | head -1)"

# ── 安装依赖 ────────────────────────────────────────────────────────────────
info "安装 Python 依赖..."
pip install -r requirements.txt
pip install pyinstaller

# FFmpeg
if command -v ffmpeg &>/dev/null; then
    info "FFmpeg 已安装: $(ffmpeg -version | head -1 | cut -d' ' -f3)"
else
    info "通过 Homebrew 安装 FFmpeg..."
    brew install ffmpeg
fi

# ── 图标检查 ────────────────────────────────────────────────────────────────
ICON_ARG=""
if [ -f assets/icon.icns ]; then
    ICON_ARG="--icon=assets/icon.icns"
    info "使用自定义图标 assets/icon.icns"
else
    warn "未找到 assets/icon.icns，使用默认图标"
    warn "参见 assets/README.md 了解如何制作图标"
fi

# ── PyInstaller 构建 ────────────────────────────────────────────────────────
info "PyInstaller 构建 .app Bundle..."

# 清理旧构建
rm -rf build/ dist/ *.spec

pyinstaller \
    --windowed \
    --name Live2Gif \
    $ICON_ARG \
    --add-binary="$(which ffmpeg):." \
    --osx-bundle-identifier=com.livetogif.app \
    main_gui.py

info ".app Bundle 构建完成"

# ── 配置 Info.plist ────────────────────────────────────────────────────────
info "配置 Info.plist（文件类型关联）..."

$PYTHON << 'PYEOF'
import plistlib
from pathlib import Path

plist_path = Path("dist/Live2Gif.app/Contents/Info.plist")

with plist_path.open("rb") as f:
    plist = plistlib.load(f)

plist["CFBundleDocumentTypes"] = [
    {
        "CFBundleTypeName": "Live Photo (HEIC)",
        "CFBundleTypeExtensions": ["heic", "HEIC"],
        "CFBundleTypeRole": "Viewer",
        "LSHandlerRank": "Alternate",
        "LSItemContentTypes": ["public.heic"],
    },
    {
        "CFBundleTypeName": "QuickTime Movie",
        "CFBundleTypeExtensions": ["mov", "MOV"],
        "CFBundleTypeRole": "Viewer",
        "LSHandlerRank": "Alternate",
        "LSItemContentTypes": ["com.apple.quicktime-movie"],
    },
]

plist["CFBundleShortVersionString"] = "1.0.0"
plist["CFBundleVersion"] = "1.0.0"
plist["NSHighResolutionCapable"] = True
plist["LSMinimumSystemVersion"] = "11.0"

with plist_path.open("wb") as f:
    plistlib.dump(plist, f)

print("✓ Info.plist 已配置")
PYEOF

# ── 创建 DMG ───────────────────────────────────────────────────────────────
info "创建 DMG 安装镜像..."

hdiutil create \
    -volname "Live2Gif" \
    -srcfolder dist/Live2Gif.app \
    -ov -format UDZO \
    Live2Gif.dmg

# ── 完成 ────────────────────────────────────────────────────────────────────
echo ""
echo "================================================"
info "构建完成！"
echo ""
echo "  产物:"
echo "    $(pwd)/dist/Live2Gif.app"
echo "    $(pwd)/Live2Gif.dmg  ($(du -h Live2Gif.dmg | cut -f1))"
echo ""
echo "  使用方式:"
echo "    open dist/Live2Gif.app         # 运行应用"
echo "    open Live2Gif.dmg              # 打开安装镜像"
echo "================================================"
