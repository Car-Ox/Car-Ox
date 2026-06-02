---
name: macos-app-packaging
description: Use when building .app bundles with PyInstaller, configuring Info.plist, creating DMG installers, or bundling FFmpeg for macOS distribution
---

# macOS 应用打包

## .app Bundle 结构

```
Live2Gif.app/
└── Contents/
    ├── MacOS/
    │   ├── Live2Gif          # PyInstaller 生成的可执行文件
    │   └── ffmpeg            # bundled 静态 FFmpeg 二进制
    ├── Resources/
    │   └── icon.icns         # 应用图标
    └── Info.plist            # 应用元数据
```

## PyInstaller 构建命令

```bash
pyinstaller \
    --windowed \
    --name Live2Gif \
    --icon=assets/icon.icns \
    --add-binary="$(which ffmpeg):." \
    --osx-bundle-identifier=com.livetogif.app \
    main_gui.py
```

关键参数：
- `--windowed`：无终端窗口的 GUI 应用
- `--add-binary`：将外部二进制（如 FFmpeg）打包进 .app
- `--osx-bundle-identifier`：macOS 唯一标识符

## Info.plist 配置

### 文件类型关联

```python
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
```

### 关键 Info.plist 键

| 键 | 值 | 说明 |
|----|-----|------|
| `CFBundleDocumentTypes` | 数组 | 文件类型关联 |
| `CFBundleShortVersionString` | "1.0.0" | Finder 中显示的版本 |
| `LSMinimumSystemVersion` | "11.0" | 最低 macOS 版本要求 |
| `NSHighResolutionCapable` | True | 支持 Retina 屏幕 |

## DMG 创建

```bash
hdiutil create \
    -volname "Live2Gif" \
    -srcfolder dist/Live2Gif.app \
    -ov -format UDZO \
    Live2Gif.dmg
```

- `-volname`：挂载后的卷名
- `-format UDZO`：压缩格式，最小体积
- `-ov`：覆盖已存在的 DMG

## 首次运行绕过 Gatekeeper

用户首次打开时需右键 → "打开" 确认。正式分发需要 Apple Developer Program ($99/年) 代码签名。

## 图标制作

```bash
mkdir Live2Gif.iconset
sips -z 16 16   icon-1024.png --out Live2Gif.iconset/icon_16x16.png
sips -z 32 32   icon-1024.png --out Live2Gif.iconset/icon_16x16@2x.png
# ... 继续 32x32, 64x64, 128x128, 256x256, 512x512 及其 @2x
iconutil -c icns Live2Gif.iconset
mv Live2Gif.icns assets/icon.icns
```

## CI 集成

```yaml
- name: 创建 DMG
  run: |
    hdiutil create -volname "Live2Gif" \
      -srcfolder dist/Live2Gif.app \
      -ov -format UDZO Live2Gif.dmg

- name: 上传产物
  uses: actions/upload-artifact@v4
  with:
    name: Live2Gif-macOS
    path: live2gif/Live2Gif.dmg
    retention-days: 30
```

## 常见陷阱

| 问题 | 修复 |
|------|------|
| `.app` 无法启动 | 检查 `MacOS/` 目录权限和 FFmpeg 二进制路径 |
| PyInstaller 找不到模块 | 检查 `working-directory` 和导入路径 |
| DMG 体积过大 | 确认不含调试符号，使用 UDZO 压缩 |
| Info.plist 无效 | 用 `plutil -lint Info.plist` 验证 |
