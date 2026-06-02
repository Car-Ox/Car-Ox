---
name: ffmpeg-mastery
description: Use when generating GIFs from video via FFmpeg palettegen/paletteuse filters, controlling quality/size/fps, using ffprobe for metadata, or debugging FFmpeg filter chains
---

# FFmpeg GIF 转换精通

## 核心滤镜链（双通道调色板）

```
MOV → 帧提取 → 调色板生成 → 调色板应用 → GIF
```

```bash
ffmpeg -i input.mov -vf \
  "fps=15,scale='min(480,iw)':'min(480,ih)':force_original_aspect_ratio=decrease,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
  -loop 0 output.gif
```

## FFmpeg 7.0+ 兼容性

**关键变更：** FFmpeg 7.0 将 `max_colors` 从 `paletteuse` 移到了 `palettegen`。

```python
# FFmpeg 7.0+（当前正确写法）
palettegen = "palettegen"
if max_colors is not None:
    palettegen = f"palettegen=max_colors={max_colors}"

vf_filter = (
    f"fps={fps},"
    f"scale='min({max_size},iw)':'min({max_size},ih)':force_original_aspect_ratio=decrease,"
    "split[a][b];"
    f"[a]{palettegen}[p];"
    "[b][p]paletteuse"
)
```

## 参数速查

| 参数 | 滤镜位置 | 典型值 | 效果 |
|------|---------|--------|------|
| `fps=N` | 开头 | 10-30 | 输出帧率 |
| `scale` | fps 之后 | min(W,H) | 等比缩放 |
| `max_colors=N` | palettegen | 64/128/256 | 调色板精度 |
| `-loop 0` | ffmpeg 参数 | 0=无限, 1=一次 | 循环模式 |

## 质量预设

```python
QUALITY_MAP = {
    "low": 64,      # 小文件，低画质
    "medium": 128,  # 平衡
    "high": 256,    # 高画质（FFmpeg 默认）
}
```

## ffprobe 元数据提取

### 获取视频尺寸

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height \
  -of csv=p=0 input.gif
# 输出: 480,320
```

### 获取帧率

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=r_frame_rate \
  -of csv=p=0 input.gif
# 输出: 15/1
```

### Python 中的路径解析

```python
ffprobe = Path(ffmpeg_path).with_name(
    "ffprobe.exe" if Path(ffmpeg_path).suffix == ".exe" else "ffprobe"
)
```

## Python subprocess 调用模板

```python
import subprocess
from pathlib import Path

cmd = [ffmpeg, "-i", str(input_path), "-vf", vf_filter,
       "-loop", loop_value, str(output_path)]

try:
    subprocess.run(cmd, check=True, capture_output=True,
                   text=True, timeout=300)
except subprocess.CalledProcessError as exc:
    raise ConversionError(exc.stderr.strip()) from exc
except subprocess.TimeoutExpired as exc:
    raise ConversionError(f"转换超时（{exc.timeout} 秒）") from exc
except OSError as exc:
    raise ConversionError(f"无法执行 FFmpeg（{exc}）") from exc
```

## 测试用视频生成

```bash
# 64x64, 0.5s, 10fps, libx264
ffmpeg -f lavfi -i "testsrc=duration=0.5:size=64x64:rate=10" \
  -c:v libx264 -pix_fmt yuv420p -y test_video.mov
```

## 常见陷阱

| 问题 | 原因 | 修复 |
|------|------|------|
| `Option 'max_colors' not found` | FFmpeg 7.0+ 移除了 paletteuse 的 max_colors | 改为 `palettegen=max_colors=N` |
| GIF 文件过大 | 未限制帧率/尺寸/颜色 | 降低 fps、max_size、max_colors |
| FFmpeg 挂起 | 损坏文件或超大输入 | 添加 `timeout=300` |
| 输出尺寸超出预期 | scale 参数语法错误 | 检查 `'min(W,iw)':'min(H,ih)'` 引号 |
