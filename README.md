# CS2 Highlight Studio v1.0.260612

CS2 自动高光检测、录制和剪辑工具  
Automatic highlight detection, recording and clipping tool for CS2.

## 功能 / Features

- 自动解析 CS2 Demo，检测 ACE / 4K / 3K 等高光片段  
  Automatically parse CS2 demos, detect highlights such as ACE, 4K, 3K.
- 通过 GSI 实时监控对局数据，自动开始/停止 OBS 录制  
  Real-time match monitoring via GSI, auto start/stop OBS recording.
- 一键导出高光片段（基于 FFmpeg）  
  One-click highlight export (based on FFmpeg).
- 智能硬件检测，自动配置 OBS 最佳录制参数  
  Smart hardware detection, auto-configure optimal OBS recording parameters.
- 自动识别 Steam ID、CS2 路径、FFmpeg 等  
  Auto-detect Steam ID, CS2 path, FFmpeg, etc.
- 对局历史记录，每个对局独立文件夹管理  
  Match history with per-match independent folder management.
- 全局快捷键支持（可自定义）  
  Global hotkey support (customizable).
- 深色主题 UI（PyQt6）  
  Dark theme UI (PyQt6).

## 环境要求 / Requirements

- Python 3.10+
- OBS Studio（启用 WebSocket 插件 / WebSocket plugin enabled）
- CS2
- FFmpeg（加入系统 PATH / added to system PATH）

## 安装 / Installation

```bash
git clone https://github.com/yourname/CS2-Highlight-Studio.git
cd CS2-Highlight-Studio
pip install -r requirements.txt
