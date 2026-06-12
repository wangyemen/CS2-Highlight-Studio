"""
Translations - Chinese / English
"""

_lang = "zh"  # default


def set_lang(code):
    global _lang
    _lang = code


def get_lang():
    return _lang


def t(key):
    """Get translated string by key."""
    d = _STRINGS.get(_lang, _STRINGS["zh"])
    return d.get(key, _STRINGS["zh"].get(key, key))


_STRINGS = {
    "zh": {
        # App
        "app_name": "CS2 高光集锦工作室",
        "app_version": "版本",

        # Sidebar
        "nav_dashboard": "仪表盘",
        "nav_demos": "Demo 库",
        "nav_editor": "集锦编辑",
        "nav_history": "对局记录",
        "nav_monitor": "实时监控",
        "nav_clipper": "视频剪辑",
        "nav_settings": "设  置",

        # Dashboard
        "dash_obs": "OBS 状态",
        "dash_gsi": "GSI 状态",
        "dash_highlights": "高光片段",
        "dash_matches": "对局数",

        # OBS
        "obs_connected": "已连接",
        "obs_recording": "录制中",
        "obs_idle": "已连接(空闲)",
        "obs_disconnected": "未连接",

        # GSI
        "gsi_receiving": "接收中",
        "gsi_waiting": "等待数据",
        "gsi_offline": "未启动",
        "gsi_gameover": "比赛结束",

        # Monitor
        "mon_map": "地图",
        "mon_score": "比分",
        "mon_round": "回合",
        "mon_health": "血量",
        "mon_kda": "K / D / A",
        "mon_phase": "阶段",

        # Clipper
        "clip_title": "视频剪辑",
        "clip_hint": "Space=播放  S=剪切  Del=删除  Ctrl+E=导出  ±=缩放",
        "clip_drop": "拖放视频到此处，或点击下方浏览",
        "clip_browse": "浏览视频文件",
        "clip_split": "S 剪切",
        "clip_delete": "Del 删除",
        "clip_export": "Ctrl+E 导出",
        "clip_fullscreen": "全屏预览",
        "clip_split_done": "已剪切 → {} 段",
        "clip_delete_done": "删除完成 → {} 段剩余",
        "clip_exporting": "导出 →",
        "clip_export_done": "完成! {} 个文件",
        "clip_export_fail": "导出失败",
        "clip_prompt_split": "请先剪切视频",
        "clip_confirm_delete": "确定要删除所有数据吗？\n\n将删除：\n• 所有对局记录\n• 所有缓存文件\n• 所有视频输出文件\n• 所有自定义设置\n\n⚠ 此操作完全不可撤销！",
        "clip_confirm_cache": "确定要清除所有缓存数据吗？\n\n包括：\n• Demo 解析缓存\n• 对局记录文件\n• 时间戳缓存\n\n不会删除设置文件",
        "clip_cache_cleared": "缓存已清除，删除 {} 个文件",
        "clip_all_cleared": "全部数据已清除，删除 {} 个文件——请重启程序",
        "clip_yes": "是",
        "clip_no": "否",

        # Settings
        "set_title": "设置",
        "set_save": "保存设置",
        "set_saved": "✓ 已保存",
        "set_auto_config": "一键自动配置 OBS",

        # Settings tabs
        "tab_general": "常规",
        "tab_obs": "OBS",
        "tab_gsi": "GSI",
        "tab_detection": "检测",
        "tab_output": "输出",
        "tab_advanced": "高级",
        "tab_about": "关于",
        "tab_language": "语言",

        # General
        "gen_user": "用户设置",
        "gen_steam_id": "用户 ID:",
        "gen_steam_ph": "你的 Steam ID (CS2 Demo 识别用)",
        "gen_auto_detect": "自动识别",
        "gen_tick_rate": "Tick Rate:",
        "gen_features": "功能开关",
        "gen_auto_record": "比赛开始时自动开始录制",
        "gen_auto_process": "比赛结束时自动处理 Demo",
        "gen_hotkeys": "启用快捷键",

        # OBS
        "obs_ws": "OBS WebSocket 连接",
        "obs_host": "地址:",
        "obs_port": "端口:",
        "obs_pass": "密码:",
        "obs_pass_ph": "WebSocket 密码 (可空)",
        "obs_auto": "启动时自动连接",
        "obs_auto_port": "自动识别端口",
        "obs_test": "测试连接",
        "obs_test_ok": "✓ 连接成功",
        "obs_test_fail": "✕ 连接失败",

        # GSI
        "gsi_config": "Game State Integration",
        "gsi_port_label": "GSI 端口:",
        "gsi_auto_start": "启动时自动开启 GSI 服务",
        "gsi_cs2_path": "CS2 路径",
        "gsi_cs2_ph": "CS2 安装目录 (可自动识别)",
        "gsi_install": "安装 GSI 配置文件",
        "gsi_install_ok": "✓ 安装成功，请重启 CS2",
        "gsi_install_fail": "✕ 未找到 CS2 cfg 目录",

        # Detection
        "det_highlights": "高光片检测参数",
        "det_min_score": "最低分数:",
        "det_min_kills": "连杀最少杀:",
        "det_clutch": "Clutch 最少杀:",
        "det_before": "片段前缀:",
        "det_after": "片段后缀:",
        "det_demo_folder": "Demo 文件夹",
        "det_demo_ph": "Demo 存放目录 (可自动识别)",

        # Output
        "out_settings": "输出设置",
        "out_dir": "输出目录:",
        "out_dir_ph": "集锦输出目录",
        "out_quality": "画质:",
        "out_format": "封装格式:",
        "out_copy": "复制模式 (无损快速导出)",
        "out_copy_tip": "直接复制原始质量，不重新编码。速度最快，但无法自定义片段。",
        "out_ffmpeg": "FFmpeg",
        "out_ffmpeg_ph": "ffmpeg 路径 (可自动识别)",

        # Advanced
        "adv_hotkeys": "热键设置",
        "adv_hk_record": "开始/停止录制",
        "adv_hk_replay": "Replay Buffer 保存",

        # About
        "about_title": "关于",
        "about_current": "当前版本:  v",
        "about_license": "— CS2 Highlight Studio · MIT License",
        "about_update": "更新",
        "about_check": "立即检查更新",
        "about_checking": "检查中...",
        "about_download": "下载更新",
        "about_downloading": "下载中...",
        "about_auto_check": "启动时自动检查更新",
        "about_notify": "有新版本时弹窗提示",
        "about_auto_dl": "有新版本时自动下载",
        "about_latest": "✓ 已是最新版本 v",
        "about_new": "↑ 有新版本: v{} (当前 v{})",
        "about_connecting": "正在连接 GitHub...",
        "about_network_err": "网络连接失败",
        "about_download_ok": "✓ 下载完成，正在启动安装...",
        "about_download_fail": "✕ 下载失败，已打开网页",
        "about_new_title": "有新版本可用",
        "about_new_text": "发现新版本 v{} → v{}",
        "about_release_notes": "更新内容:",

        # Language
        "lang_title": "语言设置",
        "lang_label": "界面语言:",
        "lang_restart": "语言将在重启后完全生效",
        "lang_zh": "中文",
        "lang_en": "English",

        # Clean
        "clean_title": "数据管理",
        "clean_warn": "清除将删除所有对局记录、缓存和设置，此操作不可撤销",
        "clean_cache": "清除缓存",
        "clean_all": "清除所有数据",

        # Toast
        "toast_gsi_missing": "GSI 配置未安装! 请在设置中安装后重启游戏",
        "toast_match_end": "比赛结束，自动停止录制",
        "toast_round1": "第1回合开始，自动开始录制",
        "toast_demo_found": "发现:",
        "toast_parse": "解析:",
        "toast_parse_done": "解析完成:",
        "toast_detect_done": "检测完成 | {} 个高光片段",
        "toast_exporting": "开始导出...",
        "toast_export_ok": "导出成功!",
        "toast_replay_saved": "Replay Buffer 已保存",
        "toast_hotkey": "快捷键:",
        "toast_clipper_hint": "拖放视频到剪辑页面",

        # Live monitor end
        "live_gameover": "比赛结束",

        # Tray
        "tray_show": "显示主窗口",
        "tray_no_record": "未录制",
        "tray_recording": "录制中...",
        "tray_connected": "已连接",
        "tray_gsi_on": "GSI: 接收中",
        "tray_gsi_off": "GSI: 未启动",
        "tray_quit": "退出程序",
        "tray_minimized": "已最小化到托盘，双击托盘图标恢复。",
    },

    "en": {
        # App
        "app_name": "CS2 Highlight Studio",
        "app_version": "Version",

        # Sidebar
        "nav_dashboard": "Dashboard",
        "nav_demos": "Demo Library",
        "nav_editor": "Highlight Editor",
        "nav_history": "Match History",
        "nav_monitor": "Live Monitor",
        "nav_clipper": "Video Clipper",
        "nav_settings": "Settings",

        # Dashboard
        "dash_obs": "OBS Status",
        "dash_gsi": "GSI Status",
        "dash_highlights": "Highlights",
        "dash_matches": "Matches",

        # OBS
        "obs_connected": "Connected",
        "obs_recording": "Recording",
        "obs_idle": "Connected (Idle)",
        "obs_disconnected": "Disconnected",

        # GSI
        "gsi_receiving": "Receiving",
        "gsi_waiting": "Waiting",
        "gsi_offline": "Offline",
        "gsi_gameover": "Match Ended",

        # Monitor
        "mon_map": "Map",
        "mon_score": "Score",
        "mon_round": "Round",
        "mon_health": "Health",
        "mon_kda": "K / D / A",
        "mon_phase": "Phase",

        # Clipper
        "clip_title": "Video Clipper",
        "clip_hint": "Space=Play  S=Split  Del=Delete  Ctrl+E=Export  ±=Zoom",
        "clip_drop": "Drop video here, or click browse below",
        "clip_browse": "Browse Video File",
        "clip_split": "S Split",
        "clip_delete": "Del Delete",
        "clip_export": "Ctrl+E Export",
        "clip_fullscreen": "Fullscreen Preview",
        "clip_split_done": "Split → {} segments",
        "clip_delete_done": "Deleted → {} segments remaining",
        "clip_exporting": "Exporting →",
        "clip_export_done": "Done! {} files",
        "clip_export_fail": "Export failed",
        "clip_prompt_split": "Please split the video first",
        "clip_confirm_delete": "Are you sure you want to delete all data?\n\nThis will delete:\n• All match records\n• All cache files\n• All video output files\n• All custom settings\n\n⚠ This action is completely irreversible!",
        "clip_confirm_cache": "Clear all cache data?\n\nIncludes:\n• Demo parse cache\n• Match history files\n• Timestamp cache\n\nSettings files will NOT be deleted",
        "clip_cache_cleared": "Cache cleared, {} files deleted",
        "clip_all_cleared": "All data cleared, {} files deleted — please restart",
        "clip_yes": "Yes",
        "clip_no": "No",

        # Settings
        "set_title": "Settings",
        "set_save": "Save Settings",
        "set_saved": "✓ Saved",
        "set_auto_config": "Auto-Configure OBS",

        # Settings tabs
        "tab_general": "General",
        "tab_obs": "OBS",
        "tab_gsi": "GSI",
        "tab_detection": "Detection",
        "tab_output": "Output",
        "tab_advanced": "Advanced",
        "tab_about": "About",
        "tab_language": "Language",

        # General
        "gen_user": "User Settings",
        "gen_steam_id": "User ID:",
        "gen_steam_ph": "Your Steam ID (for Demo recognition)",
        "gen_auto_detect": "Auto Detect",
        "gen_tick_rate": "Tick Rate:",
        "gen_features": "Feature Toggles",
        "gen_auto_record": "Auto-start recording when match begins",
        "gen_auto_process": "Auto-process Demo when match ends",
        "gen_hotkeys": "Enable global hotkeys",

        # OBS
        "obs_ws": "OBS WebSocket Connection",
        "obs_host": "Host:",
        "obs_port": "Port:",
        "obs_pass": "Password:",
        "obs_pass_ph": "WebSocket password (optional)",
        "obs_auto": "Auto-connect on startup",
        "obs_auto_port": "Auto-detect port",
        "obs_test": "Test Connection",
        "obs_test_ok": "✓ Connected",
        "obs_test_fail": "✕ Connection failed",

        # GSI
        "gsi_config": "Game State Integration",
        "gsi_port_label": "GSI Port:",
        "gsi_auto_start": "Auto-start GSI service on launch",
        "gsi_cs2_path": "CS2 Path",
        "gsi_cs2_ph": "CS2 install directory (auto-detectable)",
        "gsi_install": "Install GSI Config File",
        "gsi_install_ok": "✓ Installed, please restart CS2",
        "gsi_install_fail": "✕ CS2 cfg directory not found",

        # Detection
        "det_highlights": "Highlight Detection Parameters",
        "det_min_score": "Min Score:",
        "det_min_kills": "Min Multi-Kill:",
        "det_clutch": "Min Clutch Kills:",
        "det_before": "Clip Prefix:",
        "det_after": "Clip Suffix:",
        "det_demo_folder": "Demo Folder",
        "det_demo_ph": "Demo storage directory (auto-detectable)",

        # Output
        "out_settings": "Output Settings",
        "out_dir": "Output Directory:",
        "out_dir_ph": "Highlight output directory",
        "out_quality": "Quality:",
        "out_format": "Format:",
        "out_copy": "Copy Mode (lossless fast export)",
        "out_copy_tip": "Directly copy original quality without re-encoding. Fastest, but no custom clips.",
        "out_ffmpeg": "FFmpeg",
        "out_ffmpeg_ph": "ffmpeg path (auto-detectable)",

        # Advanced
        "adv_hotkeys": "Hotkey Settings",
        "adv_hk_record": "Start/Stop Recording",
        "adv_hk_replay": "Replay Buffer Save",

        # About
        "about_title": "About",
        "about_current": "Current Version:  v",
        "about_license": "— CS2 Highlight Studio · MIT License",
        "about_update": "Update",
        "about_check": "Check for Updates",
        "about_checking": "Checking...",
        "about_download": "Download Update",
        "about_downloading": "Downloading...",
        "about_auto_check": "Auto-check for updates on startup",
        "about_notify": "Show notification when update available",
        "about_auto_dl": "Auto-download when update available",
        "about_latest": "✓ Up to date v",
        "about_new": "↑ New version: v{} (current v{})",
        "about_connecting": "Connecting to GitHub...",
        "about_network_err": "Network connection failed",
        "about_download_ok": "✓ Download complete, launching installer...",
        "about_download_fail": "✕ Download failed, opened web page",
        "about_new_title": "Update Available",
        "about_new_text": "New version found v{} → v{}",
        "about_release_notes": "Release notes:",

        # Language
        "lang_title": "Language",
        "lang_label": "Interface Language:",
        "lang_restart": "Full effect requires restart",
        "lang_zh": "中文",
        "lang_en": "English",

        # Clean
        "clean_title": "Data Management",
        "clean_warn": "Clearing will delete all records, cache and settings. This cannot be undone.",
        "clean_cache": "Clear Cache",
        "clean_all": "Clear All Data",

        # Toast
        "toast_gsi_missing": "GSI config not installed! Install in Settings then restart game",
        "toast_match_end": "Match ended, auto-stopped recording",
        "toast_round1": "Round 1 started, auto-started recording",
        "toast_demo_found": "Found:",
        "toast_parse": "Parsing:",
        "toast_parse_done": "Parse complete:",
        "toast_detect_done": "Detection complete | {} highlights",
        "toast_exporting": "Starting export...",
        "toast_export_ok": "Export success!",
        "toast_replay_saved": "Replay Buffer saved",
        "toast_hotkey": "Hotkey:",
        "toast_clipper_hint": "Drop video to clipper page",

        # Live monitor end
        "live_gameover": "Match Ended",

        # Tray
        "tray_show": "Show Window",
        "tray_no_record": "Not Recording",
        "tray_recording": "Recording...",
        "tray_connected": "Connected",
        "tray_gsi_on": "GSI: Receiving",
        "tray_gsi_off": "GSI: Offline",
        "tray_quit": "Quit",
        "tray_minimized": "Minimized to tray. Double-click tray icon to restore.",
    }
}
