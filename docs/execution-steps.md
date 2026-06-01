# 📐 执行步骤文档

## 开发阶段总览

```
Phase 1: 项目初始化     ██████████ 完成
Phase 2: 核心引擎       ██████████ 完成 (converter + input_resolver + CLI)
Phase 3: GUI 界面       ██████████ 完成 (Tkinter)
Phase 4: 批量处理       ██████░░░░ 部分 (CLI 批量已实现)
Phase 5: 打包发布       ░░░░░░░░░░ 待开始
Phase 6: 测试与CI       ████████░░ 进行中 (测试套件已完善)
```

---

## Phase 1: 项目初始化 ✅

### 1.1 项目骨架
- [x] 创建项目目录结构
- [x] 初始化 CLAUDE.md
- [x] 创建开发日志系统
- [x] 建立文档体系
- [ ] 部署项目 skills (4个)
- [ ] 初始化 pyproject.toml
- [ ] 配置开发环境 (.gitignore, venv)
- [ ] 初始化 git 仓库

### 1.2 技能部署
- [ ] python-crossplatform-desktop.skill
- [ ] ffmpeg-mastery.skill
- [ ] macos-app-packaging.skill
- [ ] test-and-ci-driven.skill

---

## Phase 2: 核心引擎

### 2.1 Live Photo 解析模块
1. 编写 `LivePhotoParser` 类
2. 实现 .MOV + .HEIC 文件对识别
3. 实现元数据提取（拍摄时间、位置、封面帧）
4. 编写单元测试
5. 在真实设备文件上验证

### 2.2 FFmpeg 转换模块
1. 封装 FFmpeg 命令行调用
2. 实现帧提取功能
3. 实现 GIF 编码（调色板优化）
4. 实现质量控制参数
5. 编写单元测试和集成测试

### 2.3 转换管道
1. 组装完整转换管道
2. 实现管道配置系统
3. 实现进度回调机制
4. 编写管道集成测试

---

## Phase 3: GUI 界面 ✅

> **实施决策：** 使用 Tkinter 替代 PySide6，原因：零额外依赖、跨平台、打包体积小（~5MB vs ~70MB）。

### 3.1 主窗口
- [x] 使用 Tkinter 搭建主窗口 (500×300, 不可调整大小)
- [x] 实现文件选择区域（按钮 + 路径标签）
- [x] 实现参数调节面板（帧率滑块 1-30, 尺寸输入框, 质量下拉, 循环复选框）
- [x] 实现转换按钮 + 不确定模式进度条 + 状态标签
- [x] 绑定核心转换模块
- [x] 异步转换（threading 避免界面冻结）
- [x] 线程安全（参数在主线程读取后传入工作线程）
- [x] 消息队列安全更新 UI
- [ ] 拖拽文件支持（后续可选）

### 3.2 预览功能
1. 实现转换前/后对比视图
2. 实现 GIF 播放预览
3. 实现逐帧浏览

### 3.3 设置窗口
1. 默认输出路径设置
2. 默认转换参数设置
3. FFmpeg 路径配置

---

## Phase 4: 批量处理

### 4.1 批量界面
1. 文件列表组件
2. 每个文件的独立状态和进度
3. 批量开始/暂停/取消

### 4.2 后台处理
1. QThread 工作线程实现
2. 并发控制（同时 N 个任务）
3. 错误隔离（单个失败不影响其余）

---

## Phase 5: 打包发布

### 5.1 macOS 打包
1. PyInstaller 配置 (.spec 文件)
2. .app Bundle 生成
3. DMG 安装镜像制作
4. 代码签名（如需发布 App Store）
5. 应用公证 (notarization)

### 5.2 Windows 打包
1. PyInstaller 交叉配置
2. MSI/EXE 安装包生成

---

## Phase 6: 测试与 CI

### 6.1 测试体系
- [x] conftest.py 全局夹具（FFmpeg 检测、标记注册、测试视频生成）
- [x] test_converter.py — 单元测试 (10) + FFmpeg 集成测试 (8, @pytest.mark.ffmpeg)
- [x] test_input_resolver.py — 输入解析 + 边缘情况 (20)
- [x] test_cli.py — 参数解析 + 文件收集 + 主流程 (41)
- [x] test_gui.py — GUI 构造 + 参数提取 + 转换流程 + 平台工具 (38)
- [x] 测试总计: **108 passed, 9 skipped**（无 FFmpeg 环境）
- [ ] 单元测试覆盖率 > 80%（待量化）
- [ ] 性能基准测试

### 6.2 CI 流水线
- [ ] GitHub Actions 配置
- [ ] 代码检查 (lint)
- [ ] 类型检查 (mypy)
- [ ] 自动测试
- [ ] 自动构建
- [ ] 发布自动化

---

## 关键决策记录

| 日期 | 决策 | 理由 | 替代方案 |
|------|------|------|---------|
| 2026-06-01 | 选择 PySide6 | LGPL 许可更灵活 | PyQt6 (GPL) |
| 2026-06-01 | FFmpeg 通过 subprocess 调用 | 避免复杂的 C 绑定 | python-ffmpeg 库 |
| 2026-06-01 | GUI 改用 Tkinter | 零依赖、跨平台、打包体积小 | PySide6 / PyQt6 |
| 2026-06-01 | 转换参数主线程读取 | Tkinter 变量非线程安全 | 线程内直接访问 |
