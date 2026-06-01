# Assets

本目录存放 Live2Gif 的应用图标和打包资源。

## icon.icns（macOS 应用图标）

`icon.icns` 是 macOS 原生图标格式，用于 .app Bundle 和 DMG。

### 制作方法

1. 准备一张 **1024×1024** 的 PNG 图标（建议带圆角矩形遮罩）
2. 使用 `iconutil` 命令行工具转换：

```bash
# 创建临时目录存放各尺寸图标
mkdir Live2Gif.iconset

# 从原始 PNG 生成各尺寸版本（macOS 需要以下规格）
sips -z 16 16     icon-1024.png --out Live2Gif.iconset/icon_16x16.png
sips -z 32 32     icon-1024.png --out Live2Gif.iconset/icon_16x16@2x.png
sips -z 32 32     icon-1024.png --out Live2Gif.iconset/icon_32x32.png
sips -z 64 64     icon-1024.png --out Live2Gif.iconset/icon_32x32@2x.png
sips -z 128 128   icon-1024.png --out Live2Gif.iconset/icon_128x128.png
sips -z 256 256   icon-1024.png --out Live2Gif.iconset/icon_128x128@2x.png
sips -z 256 256   icon-1024.png --out Live2Gif.iconset/icon_256x256.png
sips -z 512 512   icon-1024.png --out Live2Gif.iconset/icon_256x256@2x.png
sips -z 512 512   icon-1024.png --out Live2Gif.iconset/icon_512x512.png
sips -z 1024 1024 icon-1024.png --out Live2Gif.iconset/icon_512x512@2x.png

# 打包为 .icns
iconutil -c icns Live2Gif.iconset

# 放入 assets/
mv Live2Gif.icns assets/icon.icns
rm -rf Live2Gif.iconset
```

### 当前状态

> **未提供真实图标文件。** 构建脚本在 `icon.icns` 缺失时会跳过图标参数，
> 生成的 .app 将使用系统默认图标。替换为真实图标后重新构建即可。
