"""
Main Window
"""
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QFrame, QLabel,
)
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QSystemTrayIcon

from ui.theme import get_stylesheet
from ui.widgets.sidebar import Sidebar
from ui.widgets.toast import Toast
from ui.pages.dashboard import DashboardPage
from ui.pages.demo_browser import DemoBrowserPage
from ui.pages.highlight_editor import HighlightEditorPage
from ui.pages.match_history import MatchHistoryPage
from ui.pages.live_monitor import LiveMonitorPage
from ui.pages.settings_page import SettingsPage
from ui.pages.video_clipper import VideoClipperPage

from core.workers import (
    DemoParseWorker, HighlightDetectWorker, VideoProcessWorker)
from core.match_history import MatchHistory


def _fname(fp):
    return fp.replace("\\", "/").split("/")[-1]


class MainWindow(QMainWindow):

    def __init__(self, settings, obs, gsi, watcher):
        super().__init__()
        self.settings = settings
        self.obs = obs
        self.gsi = gsi
        self.watcher = watcher

        self._current_match = None
        self._current_highlights = []
        self._current_source_video = ""
        self._current_match_id = None
        self._current_match_folder = ""

        self._auto_started = False
        self._auto_stopped = False
        self._processed_match = False
        self._last_recorded_match = 0

        self._match_history = MatchHistory()

        self._init_ui()
        self._connect_signals()
        self._start_services()
        self._init_tray()

    # ═══════════════════════════════════════
    #  UI init
    # ═══════════════════════════════════════

    def _init_ui(self):
        self.setWindowTitle("CS2 Highlight Studio")
        self.setMinimumSize(1200, 780)
        self.resize(1400, 860)
        self.setStyleSheet(get_stylesheet())

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        main.addWidget(self.sidebar)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        rl.addWidget(self._create_header())

        self.page_stack = QStackedWidget()
        self.page_stack.setStyleSheet("background: #060a10;")

        self.dashboard_page = DashboardPage(self.settings)
        self.dashboard_page.set_controllers(self.obs, self.gsi)
        self.demo_page = DemoBrowserPage(self.settings)
        self.editor_page = HighlightEditorPage(self.settings)
        self.history_page = MatchHistoryPage(
            self.settings, self._match_history)
        self.monitor_page = LiveMonitorPage(self.settings)
        self.clipper_page = VideoClipperPage(self.settings)
        self.settings_page = SettingsPage(self.settings)
        self.settings_page._obs_controller = self.obs

        for p in (self.dashboard_page, self.demo_page,
                  self.editor_page, self.history_page,
                  self.monitor_page, self.clipper_page,
                  self.settings_page):

            self.page_stack.addWidget(p)

        rl.addWidget(self.page_stack, 1)
        main.addWidget(right, 1)

        self.toast = Toast(central)

    def _create_header(self):
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(
            "QFrame{background:#0b1120;"
            "border-bottom:1px solid #1a2744;}")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 0, 24, 0)
        self.page_title = QLabel("")
        self.page_title.setStyleSheet(
            "font-size:13px;font-weight:500;"
            "color:#4a5c78;background:transparent;")
        h.addWidget(self.page_title)
        h.addStretch()
        self.header_status = QLabel("")
        self.header_status.setStyleSheet(
            "font-size:12px;color:#4a5c78;background:transparent;")
        h.addWidget(self.header_status)
        return header

    def _connect_signals(self):
        self.demo_page.parse_requested.connect(self._parse_demo)
        self.editor_page.export_requested.connect(
            self._export_highlights)
        self.dashboard_page.parse_requested.connect(
            lambda: self.sidebar._on_nav(1))
        self.dashboard_page.scan_requested.connect(
            self._on_dashboard_scan)
        self.obs.set_status_callback(self._on_obs_status)
        self.gsi.add_callback(self._on_gsi_update)

    def _start_services(self):
        # GSI
        if self.settings.get("gsi_auto_start", True):
            self.gsi.start()

        installed, detail = self.gsi.get_config_status()
        if not installed:
            from core.translations import t
            self.toast.show_message(
                t("toast_gsi_missing"), 6000)
        else:
            print("GSI config: " + detail)

        # OBS
        if self.settings.get("obs_auto_connect", True):
            self.obs.connect()

        # Watcher
        self.watcher.add_callback(self._on_watcher_event)

        # Status timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(3000)

        # Hotkeys
        self._init_hotkeys()
        # Check update on start
        self.settings_page.check_update_on_start()

    def _on_page_changed(self, i):
        from core.translations import t
        self.page_stack.setCurrentIndex(i)
        names = [
            t("nav_dashboard"), t("nav_demos"),
            t("nav_editor"), t("nav_history"),
            t("nav_monitor"), t("nav_clipper"),
            t("nav_settings")]

        self.page_title.setText(
            names[i] if i < len(names) else "")

    def _on_dashboard_scan(self):
        self.sidebar._on_nav(1)
        if hasattr(self.demo_page, '_scan_folder'):
            self.demo_page._scan_folder()

    # ═══════════════════════════════════════
    #  Hotkeys
    # ═══════════════════════════════════════

    def _init_hotkeys(self):
        from core.hotkey_manager import HotkeyManager
        self._hotkey_mgr = HotkeyManager(self.settings)
        if (self._hotkey_mgr.is_available
                and self.settings.get("hotkeys_enabled")):
            self._hotkey_mgr.load_from_settings(
                record_callback=self._hotkey_toggle,
                replay_callback=self._hotkey_replay)

    def _hotkey_toggle(self):
        if self.obs.state.connected:
            self.obs.toggle_recording()
            t = ("\u505c\u6b62\u5f55\u5236"
                 if not self.obs.state.recording
                 else "\u5f00\u59cb\u5f55\u5236")
            self.toast.show_message("\u5feb\u6377\u952e: " + t, 2000)

    def _hotkey_replay(self):
        if (self.obs.state.connected
                and self.obs.save_replay_buffer()):
            self.toast.show_message(
                "Replay Buffer \u5df2\u4fdd\u5b58", 2000)

    # ═══════════════════════════════════════
    #  Demo parse flow
    # ═══════════════════════════════════════

    def _parse_demo(self, demo_path, video_path=""):
        self._current_source_video = video_path
        self._current_match_folder = ""
        steam_id = (self.settings.get("steam_id", "")
                    if self.settings else "")
        tick_rate = (self.settings.get("tick_rate", 0)
                     if self.settings else 0)

        self.toast.show_message("解析: " + _fname(demo_path))
        self.header_status.setText("解析中...")

        self._parse_worker = DemoParseWorker(
            demo_path, steam_id=steam_id,
            tick_rate=tick_rate,
            video_path=video_path)
        self._parse_worker.progress.connect(
            lambda m: self.header_status.setText(m))
        self._parse_worker.finished.connect(self._on_parse_done)
        self._parse_worker.error.connect(
            lambda m: self.toast.show_message(
                "错误: " + m, 5000))
        self._parse_worker.start()

    def _on_parse_done(self, parsed_match):
        self._current_match = parsed_match
        mn = parsed_match.info.map_name
        k = parsed_match.total_kills
        self.header_status.setText(
            "解析完成 | {} | {} 杀".format(mn, k))
        self.toast.show_message(
            "解析完成: {}, {} 杀".format(mn, k))
        self._detect_highlights(parsed_match)

    def _detect_highlights(self, parsed_match):
        self._detect_worker = HighlightDetectWorker(
            parsed_match, self.settings)
        self._detect_worker.progress.connect(
            lambda m: self.header_status.setText(m))
        self._detect_worker.finished.connect(
            self._on_detect_done)
        self._detect_worker.error.connect(
            lambda m: self.toast.show_message(
                "错误: " + m, 5000))
        self._detect_worker.start()

    def _on_detect_done(self, highlights):
        self._current_highlights = highlights

        all_players = []
        if self._current_match:
            for ps in self._current_match.player_stats_a:
                all_players.append(ps["name"])
            for ps in self._current_match.player_stats_b:
                all_players.append(ps["name"])

            output_dir = (self.settings.get("output_dir", "")
                          if self.settings else "")
            record = self._match_history.add_match(
                self._current_match, highlights,
                output_dir=output_dir)
            self._current_match_id = record["id"]
            self._current_match_folder = record.get("output_dir", "")

        user_player = ""
        if (self._current_match
                and self._current_match
                    .info.user_name):
            user_player = (
                self._current_match.info.user_name)

        self.editor_page.set_highlights(
            highlights,
            self._current_source_video,
            all_players,
            user_player=user_player)
        self.editor_page.set_match_folder(self._current_match_folder)

        self.dashboard_page.highlights_card.set_value(str(len(highlights)))

        self.sidebar._on_nav(2)
        self.toast.show_message("检测到 {} 个高光片段".format(len(highlights)))
        self.header_status.setText("检测完成 | {} 个高光片段".format(len(highlights)))
        
    # ═══════════════════════════════════════
    #  Export flow
    # ═══════════════════════════════════════

    def _export_highlights(self, highlights, video_path,
                           output_dir):
        if not video_path or not os.path.isfile(video_path):
            self.toast.show_message(
                "视频不存在: " + str(video_path), 5000)
            return

        if self._current_match_folder:
            output_dir = self._current_match_folder

        match_name = "highlight"
        if self._current_match:
            mn = self._current_match.info.map_name
            if mn:
                match_name = mn

        quality = (self.settings.get("output_quality", "balanced")
                   if self.settings else "balanced")

        self.toast.show_message("开始导出...", 3000)
        self.header_status.setText("裁剪中...")

        self._export_worker = VideoProcessWorker(
            source_video=video_path,
            highlights=highlights,
            output_dir=output_dir,
            match_name=match_name,
            quality=quality,
            settings=self.settings,
        )
        self._export_worker.progress.connect(
            self._on_export_progress)
        self._export_worker.finished.connect(
            self._on_export_done)
        self._export_worker.error.connect(
            lambda m: self.toast.show_message(
                "导出失败: " + m, 6000))
        self._export_worker.start()

    def _on_export_progress(self, cur, tot, msg):
        self.editor_page.show_progress(cur, tot, msg)
        self.header_status.setText(msg)

    def _on_export_done(self, result):
        self.editor_page.hide_progress()
        merged = result.get("merged")
        clips = result.get("clips", [])

        if self._current_match_id:
            self._match_history.update_match(
                self._current_match_id,
                output_dir=self._current_match_folder,
                clips=clips)

        if merged and os.path.isfile(merged):
            self.toast.show_message(
                "导出成功! " + _fname(merged), 5000)
            self.header_status.setText("导出完成")
            if (self._current_match_folder
                    and os.path.isdir(self._current_match_folder)):
                if os.name == "nt":
                    os.startfile(self._current_match_folder)
        else:
            self.toast.show_message(
                "导出完成，{} 个片段".format(len(clips)), 4000)
            self.header_status.setText("导出完成")

    # ═══════════════════════════════════════
    #  Callbacks (no logic, just pass-through)
    # ═══════════════════════════════════════

    def _on_obs_status(self, state):
        pass

    def _on_gsi_update(self, state):
        pass

    def _on_watcher_event(self, event, data):
        if event == "new_demo":
            self.toast.show_message("发现: " + _fname(data))

    # ═══════════════════════════════════════
    #  Timer (main thread, all UI here)
    # ═══════════════════════════════════════

    def _update_status(self):
        gsi = self.gsi.state
        gsi_rx = self.gsi.is_gsi_receiving()
        
        # ── Tray status ──
        if hasattr(self, '_tray'):
            if self.obs.state.recording:
                self._tray_rec_action.setText(
                    "\u5f55\u5236\u4e2d...")
                self._tray_rec_action.setEnabled(
                    False)
                self._tray.setToolTip(
                    "CS2 Highlight Studio "
                    "- \u5f55\u5236\u4e2d")
            elif self.obs.state.connected:
                self._tray_rec_action.setText(
                    "\u5df2\u8fde\u63a5")
                self._tray.setToolTip(
                    "CS2 Highlight Studio "
                    "- \u5df2\u8fde\u63a5")
            else:
                self._tray_rec_action.setText(
                    "\u672a\u5f55\u5236")
                self._tray.setToolTip(
                    "CS2 Highlight Studio")

            if gsi_rx:
                self._tray_gsi_action.setText(
                    "GSI: \u63a5\u6536\u4e2d")
            else:
                self._tray_gsi_action.setText(
                    "GSI: \u672a\u542f\u52a8")

        
        # ── Sidebar ──
        self.sidebar.set_obs_status(
            self.obs.state.connected,
            self.obs.state.recording)

        gsi_info = ""
        if gsi_rx:
            if gsi.map_phase == "gameover":
                gsi_info = "比赛结束"
            elif gsi.match_started:
                gsi_info = "{} {}-{}".format(
                    gsi.map_name,
                    gsi.score_ct,
                    gsi.score_t)
        self.sidebar.set_gsi_status(
            gsi.connected or gsi_rx, gsi_info)

        # ── Dashboard ──
        self.dashboard_page.obs_card.set_value(
            self.obs.get_status_text(),
            "#ff3b5c" if self.obs.state.recording else
            "#00e68a" if self.obs.state.connected else "#4a5c78")

        if gsi_rx:
            gv, gc = "接收中", "#00e68a"
        elif gsi.connected:
            gv, gc = "等待数据", "#ff9f43"
        else:
            gv, gc = "未启动", "#4a5c78"
        self.dashboard_page.gsi_card.set_value(gv, gc)

        # ── Monitor cards ──
        if gsi_rx:
            self.monitor_page.card_map.set_value(
                gsi.map_name or "—", "#00b4ff")
            self.monitor_page.card_score.set_value(
                "{} : {}".format(gsi.score_ct, gsi.score_t),
                "#ff9f43")
            rn = (str(gsi.round_num)
                  if gsi.round_num > 0 else "—")
            self.monitor_page.card_round.set_value(
                rn, "#8b5cf6")

            hp = (gsi.player_health
                  if gsi.player_health > 0 else "—")
            hp_c = "#ff3b5c"
            if isinstance(hp, int) and hp > 20:
                hp_c = ("#ff9f43" if hp <= 50
                        else "#00e68a")
            self.monitor_page.card_health.set_value(
                hp, hp_c)

            self.monitor_page.card_kda.set_value(
                "{} / {} / {}".format(
                    gsi.kills, gsi.deaths, gsi.assists),
                "#00e68a")

            phase = (gsi.round_phase or gsi.map_phase
                     or "—")
            self.monitor_page.card_phase.set_value(
                phase, "#8b99b0")

        elif gsi.map_phase == "gameover" or gsi.match_ended:
            # Match ended - show summary
            self.monitor_page.card_score.set_value(
                "{} : {}".format(gsi.score_ct, gsi.score_t),
                "#ff9f43")
            self.monitor_page.card_kda.set_value(
                "{} / {} / {}".format(
                    gsi.kills, gsi.deaths, gsi.assists),
                "#00e68a")
            self.monitor_page.card_phase.set_value(
                "比赛结束", "#ff9f43")


        # ═════════════════════════════════════
        #  Auto-record (match-number based)
        # ═════════════════════════════════════

        if self.settings.get(
                "auto_record_on_match_start", False):

            # Auto-start: new match AND not yet
            # recorded for this match
            if (gsi_rx
                    and gsi.match_number > 0
                    and gsi.match_number
                        > self._last_recorded_match
                    and gsi.round_num >= 0
                    and gsi.map_phase != "warmup"
                    and gsi.round_phase
                        in ("freezetime", "live")
                    and not self._auto_started
                    and self.obs.state.connected
                    and not self.obs.state.recording):
                if self.obs.start_recording():
                    self._auto_started = True
                    self._last_recorded_match = (
                        gsi.match_number)
                    self.toast.show_message(
                        "第{}局开始，自动开始录制".format(
                            gsi.match_number),
                        3000)

            # Auto-stop when match ends
            if (gsi.match_ended
                    and self.obs.state.recording
                    and not self._auto_stopped):
                self.obs.stop_recording()
                self._auto_stopped = True
                self._auto_started = False
                self.toast.show_message(
                    "比赛结束，自动停止录制", 3000)

            # Reset on new warmup (ready for next)
            if (gsi.map_phase == "warmup"
                    and self._auto_stopped):
                self._auto_started = False
                self._auto_stopped = False

            # Reset when game exits
            if (not gsi_rx
                    and not gsi.connected
                    and self._auto_started):
                self._auto_started = False
                self._auto_stopped = False
                self._last_recorded_match = 0
            
    # ═══════════════════════════════════════
    #  System Tray
    # ═══════════════════════════════════════

    def _init_tray(self):
        from PyQt6.QtWidgets import (
            QSystemTrayIcon, QMenu)
        from PyQt6.QtGui import QAction
        from core.translations import t
        try:
            from assets.icon import get_tray_icon
            icon = get_tray_icon()
        except Exception:
            from PyQt6.QtGui import QIcon
            icon = QIcon()

        self._tray = QSystemTrayIcon(icon, self)
        self._tray.setToolTip(t("app_name"))

        menu = QMenu()

        act_show = QAction(t("tray_show"), menu)
        act_show.triggered.connect(self._tray_show)
        menu.addAction(act_show)

        menu.addSeparator()

        self._tray_rec_action = QAction(
            t("tray_no_record"), menu)
        self._tray_rec_action.setEnabled(False)
        menu.addAction(self._tray_rec_action)

        self._tray_gsi_action = QAction(
            t("tray_gsi_off"), menu)
        self._tray_gsi_action.setEnabled(False)
        menu.addAction(self._tray_gsi_action)

        menu.addSeparator()

        act_quit = QAction(t("tray_quit"), menu)
        act_quit.triggered.connect(self._tray_quit)
        menu.addAction(act_quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(
            self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if (reason
                == QSystemTrayIcon.ActivationReason
                .DoubleClick):
            self._tray_show()

    def _tray_show(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_quit(self):
        self._tray.hide()
        if self.gsi:
            self.gsi.stop()
        if self.obs:
            self.obs.disconnect()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def closeEvent(self, event):
        """Override close to minimize to tray."""
        if not hasattr(self, '_tray'):
            event.accept()
            return
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "CS2 Highlight Studio",
            "\u5df2\u6700\u5c0f\u5316\u5230\u6258\u76d8"
            "\uff0c\u53cc\u51fb\u6258\u76d8\u56fe\u6807"
            "\u6062\u590d\u3002",
            QSystemTrayIcon.MessageIcon.Information,
            2000)
