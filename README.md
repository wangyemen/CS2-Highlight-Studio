# CS2 Highlight Studio v1.0.260612

CS2 自动高光检测、录制和剪辑工具
Automatic highlight detection, recording and clipping tool for CS2.

---

## 功能 / Features

- **Demo 解析 & 高光检测** — 自动解析 CS2 Demo，检测 ACE / 4K / 3K / Clutch 等高光片段
  Automatically parse CS2 demos, detect highlights such as ACE, 4K, 3K, Clutch.

- **实时监控 & 自动录制** — 通过 GSI 实时监控对局数据，热身结束自动开始 OBS 录制，比赛结束自动停止
  Real-time match monitoring via GSI, auto start/stop OBS recording.

- **一键导出高光片段** — 基于 FFmpeg 流复制模式，无损高速导出
  One-click highlight export with FFmpeg stream copy (lossless & fast).

- **在线视频剪辑** — 内置精简版视频编辑器，支持剪切、删除、预览，类似剪映操作方式
  Built-in video clipper with split, delete, preview — JianYing-style editing.

- **智能硬件检测** — 自动检测 GPU/CPU 型号，一键配置 OBS 最佳录制参数
  Smart hardware detection, auto-configure optimal OBS recording parameters.

- **自动识别环境** — Steam ID、CS2 路径、FFmpeg、OBS WebSocket 端口自动识别
  Auto-detect Steam ID, CS2 path, FFmpeg, OBS WebSocket port.

- **对局历史记录** — 每个对局独立文件夹管理，记录 KDA、比分、高光片段
  Match history with per-match folder management, recording KDA, scores, highlights.

- **全局快捷键** — 可自定义快捷键，支持录制控制和 Replay Buffer 保存
  Global hotkey support (customizable), including recording toggle and replay buffer save.

- **系统托盘** — 关闭窗口最小化到托盘，后台持续运行
  Minimize to system tray, run in background.

- **自动更新** — 内置 GitHub 更新检查，支持一键下载新版本
  Built-in GitHub update checker with one-click download.

- **深色主题 UI** — 基于 PyQt6 的专业深色界面
  Professional dark theme UI (PyQt6).

---

## 环境要求 / Requirements

| 依赖 / Dependency | 要求 / Requirement |
|------|------|
| Python | 3.10+ |
| OBS Studio | 需启用 WebSocket 插件 (v5+) / WebSocket plugin enabled (v5+) |
| CS2 | Steam 版本 / Steam version |
| FFmpeg | 	加入系统 PATH 或在设置中指定路径 / Added to system PATH or custom path in settings |

---

## 安装 / Installation

```bash
# 克隆仓库 / Clone repository
git clone https://github.com/wangyemen/CS2-Highlight-Studio.git
cd CS2-highlight-Studio

# 安装依赖 / Install dependencies
pip install -r requirements.txt

# 运行 / Run
python main.py
```
---

## 快速开始 / Quick Start

1. 首次运行 — 程序会自动检测 Steam ID、CS2 路径、FFmpeg，未找到的可在设置中手动配置 / 
First run — Auto-detects Steam ID, CS2 path, FFmpeg; missing items can be manually configured in Settings.

2. 安装 GSI — 在设置 → GSI 页签，点击“安装 GSI 配置文件”，然后重启 CS2 / 
Install GSI — In Settings → GSI tab, click “Install GSI config file”, then restart CS2.

3. 连接 OBS — 在设置 → OBS 页签，填入 WebSocket 端口和密码，点击“测试连接” / 
Connect OBS — In Settings → OBS tab, enter WebSocket port and password, click “Test Connection”.

4. 开启自动录制 — 在设置 → 常规页签，勾选“比赛开始时自动开始录制” / 
Enable auto-recording — In Settings → General tab, check “Auto-start recording when match begins”.

5. 解析 Demo — 在 Demo 库页面，拖入 .dem 文件或点击浏览选择 / 
Parse Demo — In Demo Library page, drag & drop .dem file or click browse to select.

6. 导出高光 — 检测完成后，在集锦编辑页面调整参数，点击导出 / 
Export highlights — After detection, adjust parameters in Highlight Editor page, click Export.

---
## 项目结构 / Project Structure

```text
CS2-Highlight-Studio/
├── main.py                    # 程序入口 / Entry point
├── requirements.txt           # Python 依赖 / Dependencies
├── core/
│   ├── obs_controller.py      # OBS WebSocket 控制 / OBS WebSocket control
│   ├── gsi_server.py          # GSI 数据接收服务 / GSI data receiver
│   ├── match_watcher.py       # Demo 文件监听 / Demo file watcher
│   ├── match_history.py       # 对局历史记录 / Match history
│   ├── hardware_detector.py   # 硬件自动检测 / Hardware auto-detection
│   ├── video_processor.py     # FFmpeg 视频处理 / FFmpeg video processing
│   ├── demo_parser.py         # CS2 Demo 解析 / CS2 demo parser
│   ├── highlight_detector.py  # 高光片段检测 / Highlight detection
│   ├── hotkey_manager.py      # 全局快捷键 / Global hotkey manager
│   ├── updater.py             # 自动更新检查 / Auto-update checker
│   └── workers.py             # 后台工作线程 / Background workers
├── config/
│   └── settings.py            # 设置管理 / Settings management
├── ui/
│   ├── main_window.py         # 主窗口 / Main window
│   ├── theme.py               # 深色主题样式 / Dark theme style
│   ├── widgets/
│   │   ├── sidebar.py         # 侧边导航栏 / Sidebar navigation
│   │   ├── glow_button.py     # 发光按钮组件 / Glow button widget
│   │   ├── toast.py           # 弹窗提示 / Toast notification
│   │   └── timeline.py        # 视频剪辑时间轴 / Video editing timeline
│   └── pages/
│       ├── dashboard.py       # 仪表盘 / Dashboard
│       ├── demo_browser.py    # Demo 库 / Demo library
│       ├── highlight_editor.py# 集锦编辑 / Highlight editor
│       ├── match_history.py   # 对局记录 / Match history
│       ├── live_monitor.py    # 实时监控 / Live monitor
│       ├── video_clipper.py   # 视频剪辑 / Video clipper
│       └── settings_page.py   # 设置 / Settings
└── assets/
    └── icon.png               # 应用图标 / App icon
```

---

## 快捷键 / Shortcuts

| 快捷键 / Shortcuts | 功能 / Function |
|--------|------|
| F9 | 开始/停止录制（可自定义） / Start/stop recording (customizable) |
| F10 | 保存 Replay Buffer（可自定义） / Save replay buffer (customizable) |
| Space | 视频剪辑 — 播放/暂停 / Video clip — Play/Pause |
| S | 视频剪辑 — 在光标位置剪切 / Video clip — Split at cursor |
| Delete | 视频剪辑 — 删除选中片段 / Video clip — Delete selected segment |
| Ctrl+E | 视频剪辑 — 导出片段 / Video clip — Export selected segments |
| ← → | 视频剪辑 — 光标移动 2 秒 / Video clip — Move cursor ±2 seconds |
| + - | 视频剪辑 — 缩放时间轴 / Video clip — Zoom timeline in/out |

---

## GSI 配置 / GSI Configuration

程序会自动安装 GSI 配置文件到 CS2 目录。如果自动安装失败，手动操作： / 
The program auto-installs GSI config file to CS2 directory. If auto-install fails, do manually:

1. 将以下内容保存为 gamestate_integration_cs2highlight.cfg / 
Save the following content as gamestate_integration_cs2highlight.cfg

2. 放入 CS2 安装目录的 game/csgo/cfg 或 game/cs2/cfg 文件夹 / 
Place it in CS2 installation directory under game/csgo/cfg or game/cs2/cfg

3. 重启 CS2 / Restart CS2

```text
"CS2 Highlight Studio"
{
    "uri"       "http://127.0.0.1:3010/"
    "timeout"   "5.0"
    "buffer"    "0.1"
    "throttle"  "0.5"
    "heartbeat" "30.0"
    "data"
    {
        "provider"            "1"
        "map"                 "1"
        "round"               "1"
        "player_id"           "1"
        "player_state"        "1"
        "player_weapons"      "1"
        "player_match_stats"  "1"
    }
}
```

---

## 常见问题 / FAQ

**Q: OBS 连接失败？ / OBS connection failed?**  
A: 确认 OBS 已启用 WebSocket 服务器（工具 → WebSocket 服务器设置 → 启动服务器），端口和密码与设置中一致。  /
   Make sure OBS WebSocket server is enabled (Tools → WebSocket Server Settings → Start Server) and port/password match settings.

**Q: GSI 未连接？ / GSI not connected?**  
A: 确认 GSI 配置文件已安装到正确目录，且 CS2 已重启。程序底部状态栏会显示 GSI 连接状态。  /
   Verify GSI config file is installed in the correct directory and CS2 is restarted. The status bar shows GSI connection state.

**Q: 导出视频很慢？ / Export slow?**  
A: 程序默认使用流复制模式（`-c copy`），不重编码，速度很快。如果仍然慢，检查 FFmpeg 是否正确安装。  /
   The program uses stream copy mode (`-c copy`) by default, no re-encoding, very fast. If still slow, check FFmpeg installation.

**Q: Demo 解析失败？ / Demo parsing failed?**  
A: 确认 Steam ID 已正确填写（可在设置中点击“自动识别”），Demo 文件完整未损坏。  /
   Make sure Steam ID is correct (click “Auto-detect” in Settings), and the demo file is not corrupted.

**Q: 快捷键不响应？ / Hotkeys not working?**  
A: 确认在设置 → 常规中勾选了“启用快捷键”，且快捷键未与其他软件冲突。  /
   Check “Enable hotkeys” in Settings → General tab, and ensure no conflict with other software.

---

## 技术栈 / Tech Stack

- 语言 / Language: Python 3.10+
- UI 框架 / UI Framework: PyQt6
- 视频处理 / Video Processing: FFmpeg / FFprobe
- 数据源 / Data Source: CS2 Game State Integration (GSI)
- OBS 控制 / OBS Control: obs-websocket-python
- Demo 解析 / Demo Parsing: demoparser2
- 自动更新 / Auto-update: GitHub Raw API

---

## 许可证 / License

MIT License

---

致谢 / Acknowledgments

demoparser2
 — CS2 Demo 解析库
obsws-python
 — OBS WebSocket Python 绑定
FFmpeg
 — 视频处理引擎

---

### 改动点

| 新增内容 | 说明 |
|---------|------|
| 功能列表重写 | 每个功能加了中英文双语描述，突出亮点 |
| 环境要求改为表格 | 更清晰 |
| 快速开始 | 5 步上手指南，新用户一看就懂 |
| 项目结构 | 完整目录树，开发者快速了解代码 |
| 快捷键表格 | 所有快捷键一览 |
| GSI 配置说明 | 手动安装步骤 + 完整 cfg 内容 |
| FAQ | 5 个最常见问题和解决方案 |
| 技术栈 | 一目了然的技术依赖 |
| 致谢 | 开源项目 credit |