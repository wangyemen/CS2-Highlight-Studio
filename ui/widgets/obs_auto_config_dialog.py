"""
OBS Auto-Configuration Dialog
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QMessageBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.hardware_detector import HardwareDetector


class _DetectThread(QThread):
    done = pyqtSignal(object)

    def run(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        profile = HardwareDetector.detect_all(app)
        self.done.emit(profile)


class _ApplyThread(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, client, rec):
        super().__init__()
        self.client = client
        self.rec = rec

    def run(self):
        ok, msg = HardwareDetector.apply_to_obs(self.client, self.rec)
        self.done.emit(ok, msg)


class OBSAutoConfigDialog(QDialog):

    def __init__(self, obs_controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OBS 自动配置")
        self.setMinimumSize(640, 580)
        self.setStyleSheet("""
            QDialog { background: #080c14; }
            QLabel { color: #e8edf5; background: transparent; }
        """)
        self._obs = obs_controller
        self._profile = None
        self._rec = None
        self._build()
        self._start_detect()

    # ═══════════════════════════════════════
    #  UI
    # ═══════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Title
        t = QLabel("OBS 自动配置")
        t.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 22px; font-weight: 700; "
            "color: #e8edf5;")
        root.addWidget(t)

        sub = QLabel("检测硬件并自动设置 OBS 最佳录制参数")
        sub.setStyleSheet("font-size: 13px; color: #4a5c78;")
        root.addWidget(sub)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        inner = QFrame()
        inner.setStyleSheet("background: transparent;")
        self._inner_layout = QVBoxLayout(inner)
        self._inner_layout.setSpacing(12)

        # Loading
        self._loading = QLabel("正在检测硬件...")
        self._loading.setStyleSheet(
            "font-size: 14px; color: #00b4ff; padding: 20px;")
        self._loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._inner_layout.addWidget(self._loading)

        # Hardware info (hidden until detected)
        self._hw_frame = QFrame()
        self._hw_frame.setStyleSheet("""
            QFrame { background: #111a2e; border: 1px solid #1a2744;
            border-radius: 10px; }
        """)
        hw_layout = QGridLayout(self._hw_frame)
        hw_layout.setContentsMargins(18, 14, 18, 14)
        hw_layout.setSpacing(8)

        hw_title = QLabel("检测到的硬件")
        hw_title.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 14px; font-weight: 600; "
            "color: #00b4ff;")
        hw_layout.addWidget(hw_title, 0, 0, 1, 2)

        self._hw_labels = {}
        hw_rows = [
            ("gpu",    "显卡"),
            ("vram",   "显存"),
            ("tier",   "性能等级"),
            ("cpu",    "处理器"),
            ("threads","线程数"),
            ("ram",    "内存"),
            ("screen", "显示器"),
        ]
        for i, (key, name) in enumerate(hw_rows):
            row = i + 1
            lbl = QLabel(name)
            lbl.setStyleSheet(
                "font-size: 12px; color: #8b99b0; background: transparent;")
            hw_layout.addWidget(lbl, row, 0)
            val = QLabel("—")
            val.setStyleSheet(
                "font-size: 13px; font-weight: 600; color: #e8edf5; "
                "background: transparent;")
            hw_layout.addWidget(val, row, 1)
            self._hw_labels[key] = val

        self._hw_frame.setVisible(False)
        self._inner_layout.addWidget(self._hw_frame)

        # Recommended settings (hidden until detected)
        self._rec_frame = QFrame()
        self._rec_frame.setStyleSheet("""
            QFrame { background: #111a2e; border: 1px solid #1a2744;
            border-radius: 10px; border-top: 2px solid #00e68a; }
        """)
        rec_layout = QGridLayout(self._rec_frame)
        rec_layout.setContentsMargins(18, 14, 18, 14)
        rec_layout.setSpacing(8)

        rec_title = QLabel("推荐配置")
        rec_title.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 14px; font-weight: 600; "
            "color: #00e68a;")
        rec_layout.addWidget(rec_title, 0, 0, 1, 2)

        self._rec_labels = {}
        rec_rows = [
            ("encoder",  "录制编码器"),
            ("preset",   "预设"),
            ("rc",       "码率控制"),
            ("quality",  "质量"),
            ("out_res",  "输出分辨率"),
            ("fps",      "帧率"),
            ("format",   "封装格式"),
            ("audio",    "音频码率"),
        ]
        for i, (key, name) in enumerate(rec_rows):
            row = i + 1
            lbl = QLabel(name)
            lbl.setStyleSheet(
                "font-size: 12px; color: #8b99b0; background: transparent;")
            rec_layout.addWidget(lbl, row, 0)
            val = QLabel("—")
            val.setStyleSheet(
                "font-size: 13px; font-weight: 600; color: #e8edf5; "
                "background: transparent;")
            rec_layout.addWidget(val, row, 1)
            self._rec_labels[key] = val

        self._rec_frame.setVisible(False)
        self._inner_layout.addWidget(self._rec_frame)

        self._inner_layout.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_apply = QPushButton("应用配置")
        self._btn_apply.setFixedSize(140, 38)
        self._btn_apply.setStyleSheet("""
            QPushButton {
                background: #00e68a; color: #080c14;
                font-family: 'Exo 2'; font-size: 13px; font-weight: 700;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background: #00cc7a; }
            QPushButton:pressed { background: #00b36b; }
        """)
        self._btn_apply.clicked.connect(self._on_apply)
        self._btn_apply.setVisible(False)
        btn_row.addWidget(self._btn_apply)

        self._btn_close = QPushButton("关闭")
        self._btn_close.setFixedSize(100, 38)
        self._btn_close.setStyleSheet("""
            QPushButton {
                background: #1a2744; color: #8b99b0;
                font-size: 13px; border: 1px solid #2a3a5c;
                border-radius: 8px;
            }
            QPushButton:hover { background: #223050; color: #e8edf5; }
        """)
        self._btn_close.clicked.connect(self.close)
        btn_row.addWidget(self._btn_close)

        root.addLayout(btn_row)

    # ═══════════════════════════════════════
    #  Detection
    # ═══════════════════════════════════════

    def _start_detect(self):
        self._thread = _DetectThread()
        self._thread.done.connect(self._on_detected)
        self._thread.start()

    def _on_detected(self, profile):
        self._profile = profile
        self._rec = HardwareDetector.recommend(profile)

        self._loading.setVisible(False)
        self._fill_hw(profile)
        self._fill_rec(self._rec)
        self._hw_frame.setVisible(True)
        self._rec_frame.setVisible(True)
        self._btn_apply.setVisible(True)

    def _fill_hw(self, p):
        g = p.gpu
        tier_map = {"high": "高", "medium": "中", "low": "低", "none": "无独显"}
        tier_color = {
            "high": "#00e68a", "medium": "#ff9f43",
            "low": "#ff3b5c", "none": "#4a5c78"}

        self._hw_labels["gpu"].setText(g.name or "未检测到")
        vram = "{} MB".format(g.vram_mb) if g.vram_mb else "—"
        self._hw_labels["vram"].setText(vram)

        tier_text = tier_map.get(g.tier, g.tier)
        tc = tier_color.get(g.tier, "#8b99b0")
        self._hw_labels["tier"].setText(tier_text)
        self._hw_labels["tier"].setStyleSheet(
            "font-size:13px;font-weight:700;color:{};"
            "background:transparent;".format(tc))

        self._hw_labels["cpu"].setText(p.cpu_name[:40])
        self._hw_labels["threads"].setText(str(p.cpu_threads))
        self._hw_labels["ram"].setText("{} GB".format(p.ram_gb))
        self._hw_labels["screen"].setText(
            "{} x {}".format(p.display_w, p.display_h))

    def _fill_rec(self, r):
        self._rec_labels["encoder"].setText(r["encoder"])

        preset = r.get("preset", "—")
        self._rec_labels["preset"].setText(preset)

        rc = r.get("rc", "—")
        self._rec_labels["rc"].setText(rc)

        quality = "—"
        if rc in ("CQP", "ICQ"):
            quality = "CQ {} (越低越好)".format(r.get("cq_level", "?"))
        elif rc == "CBR":
            quality = "{} Kbps".format(r.get("bitrate", r.get("max_bitrate", "?")))
        self._rec_labels["quality"].setText(quality)

        self._rec_labels["out_res"].setText(
            "{} x {}".format(r["out_w"], r["out_h"]))
        self._rec_labels["fps"].setText(str(r["fps"]))
        self._rec_labels["format"].setText(r["format"].upper())
        self._rec_labels["audio"].setText(
            "{} Kbps AAC".format(r["audio_bitrate"]))

    # ═══════════════════════════════════════
    #  Apply
    # ═══════════════════════════════════════

    def _on_apply(self):
        if not self._rec:
            return
        if not self._obs or not self._obs.state.connected:
            QMessageBox.warning(
                self, "未连接",
                "请先在设置中连接 OBS WebSocket。")
            return

        if self._obs.state.recording:
            ret = QMessageBox.question(
                self, "正在录制",
                "OBS 正在录制中，应用配置可能需要先停止录制。\n\n"
                "是否停止录制并应用配置？",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.Yes:
                self._obs.stop_recording()
            else:
                return

        self._btn_apply.setEnabled(False)
        self._btn_apply.setText("应用中...")

        self._apply_thread = _ApplyThread(
            self._obs._client, self._rec)
        self._apply_thread.done.connect(self._on_applied)
        self._apply_thread.start()

    def _on_applied(self, ok, msg):
        self._btn_apply.setEnabled(True)
        self._btn_apply.setText("应用配置")

        if ok:
            QMessageBox.information(self, "完成", msg)
        else:
            QMessageBox.warning(self, "部分失败", msg)
