"""
Settings Page - with auto-detection
"""
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QComboBox,
    QScrollArea, QFormLayout, QMessageBox,
    QFileDialog, QSpinBox, QCheckBox,
    QStackedWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.translations import t, set_lang, get_lang

class SettingsCard(QFrame):

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame { background: #111a2e;
            border: 1px solid #1a2744;
            border-radius: 12px; }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(12)
        if title:
            t = QLabel(title)
            t.setStyleSheet(
                "font-family: 'Exo 2'; "
                "font-size: 15px; font-weight: 600; "
                "color: #e8edf5; "
                "background: transparent;")
            self._layout.addWidget(t)

    def addWidget(self, w):
        self._layout.addWidget(w)

    def addLayout(self, l):
        self._layout.addLayout(l)


class SettingsPage(QWidget):

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._obs_controller = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "background: transparent;")

        container = QWidget()
        container.setStyleSheet(
            "background: transparent;")
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(32, 24, 32, 24)
        self._layout.setSpacing(16)

        title = QLabel("\u8bbe\u7f6e")
        title.setObjectName("heading")
        self._layout.addWidget(title)

        self.tabs = QStackedWidget()
        self._build_general_tab()
        self._build_obs_tab()
        self._build_gsi_tab()
        self._build_detection_tab()
        self._build_output_tab()
        self._build_advanced_tab()
        self._build_about_tab()
        self._layout.addWidget(self.tabs, 1)

        # Tab nav
        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)
        self._nav_buttons = []
        tab_names = [
            "\u5e38\u89c4", "OBS", "GSI",
            "\u68c0\u6d4b", "\u8f93\u51fa",
            "\u9ad8\u7ea7", "\u5173\u4e8e"]
        for i, name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.clicked.connect(
                lambda _, idx=i: self._switch_tab(idx))
            nav_row.addWidget(btn)
            self._nav_buttons.append(btn)
        nav_row.addStretch()
        self._layout.addLayout(nav_row)

        # Buttons
        save_row = QHBoxLayout()
        save_row.addStretch()

        auto_btn = QPushButton(
            "\u26a1 \u4e00\u952e\u81ea\u52a8\u914d\u7f6e OBS")
        auto_btn.setFixedHeight(38)
        auto_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00b4ff, stop:1 #00e68a);
                color: #080c14;
                font-family: 'Exo 2';
                font-size: 13px; font-weight: 700;
                border: none; border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00c8ff, stop:1 #00ff9a);
            }
        """)
        auto_btn.clicked.connect(self._open_auto_config)
        save_row.addWidget(auto_btn)

        self._btn_save = QPushButton("\u4fdd\u5b58\u8bbe\u7f6e")
        self._btn_save.setFixedSize(120, 38)
        self._btn_save.setStyleSheet("""
            QPushButton {
                background: #00b4ff; color: #080c14;
                font-family: 'Exo 2';
                font-size: 13px; font-weight: 700;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background: #00c8ff; }
        """)
        self._btn_save.clicked.connect(self._on_save)
        save_row.addWidget(self._btn_save)
        self._layout.addLayout(save_row)

        scroll.setWidget(container)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._init_fields()
        self._switch_tab(0)

    def _switch_tab(self, i):
        self.tabs.setCurrentIndex(i)
        for j, btn in enumerate(self._nav_buttons):
            btn.setChecked(j == i)
            if j == i:
                btn.setStyleSheet(
                    "QPushButton { background: #00b4ff;"
                    " color: #080c14; font-weight: 700;"
                    " border: none; border-radius: 8px;"
                    " padding: 0 16px; }")
            else:
                btn.setStyleSheet(
                    "QPushButton { background: #1a2744;"
                    " color: #8b99b0; "
                    "border: 1px solid #2a3a5c; "
                    "border-radius: 8px; "
                    "padding: 0 16px; }"
                    "QPushButton:hover { "
                    "background: #223050; "
                    "color: #e8edf5; }")

    # ═══════════════════════════════════════
    #  General tab
    # ═══════════════════════════════════════

    def _build_general_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard("\u7528\u6237\u8bbe\u7f6e")
        form = QFormLayout()
        form.setSpacing(10)

        sid_row = QHBoxLayout()
        self.field_steam_id = QLineEdit()
        self.field_steam_id.setPlaceholderText(
            "\u4f63\u7684 Steam ID "
            "(CS2 Demo \u8bc6\u522b\u7528)")
        btn_sid = QPushButton("\u81ea\u52a8\u8bc6\u522b")
        btn_sid.setFixedWidth(90)
        btn_sid.clicked.connect(
            self._auto_detect_steam_id)
        sid_row.addWidget(self.field_steam_id, 1)
        sid_row.addWidget(btn_sid)
        form.addRow("\u7528\u6237 ID:", sid_row)

        tr_row = QHBoxLayout()
        self.field_tick_rate = QComboBox()
        self.field_tick_rate.addItems(
            ["64", "128", "Auto"])
        tr_row.addWidget(self.field_tick_rate)
        tr_row.addStretch()
        form.addRow("Tick Rate:", tr_row)

        card.addLayout(form)
        layout.addWidget(card)

        card2 = SettingsCard("\u529f\u80fd\u5f00\u5173")
        self.field_auto_record = QCheckBox(
            "\u6bd4\u8d5b\u5f00\u59cb\u65f6"
            "\u81ea\u52a8\u5f00\u59cb\u5f55\u5236")
        self.field_auto_process = QCheckBox(
            "\u6bd4\u8d5b\u7ed3\u675f\u65f6"
            "\u81ea\u52a8\u5904\u7406 Demo")
        self.field_hotkeys = QCheckBox(
            "\u542f\u7528\u5feb\u6377\u952e")
        card2.addWidget(self.field_auto_record)
        card2.addWidget(self.field_auto_process)
        card2.addWidget(self.field_hotkeys)
        layout.addWidget(card2)

        layout.addStretch()
        self.tabs.addWidget(page)

    def _auto_detect_steam_id(self):
        from core.hardware_detector import \
            HardwareDetector
        sid = HardwareDetector.detect_steam_id()
        if sid:
            self.field_steam_id.setText(sid)
            QMessageBox.information(
                self, "\u8bc6\u522b\u6210\u529f",
                "Steam ID: " + sid)
        else:
            QMessageBox.warning(
                self, "\u672a\u627e\u5230",
                "\u672a\u80fd\u81ea\u52a8\u8bc6\u522b "
                "Steam ID\n\u8bf7\u624b\u52a8\u8f93\u5165")

    # ═══════════════════════════════════════
    #  OBS tab
    # ═══════════════════════════════════════

    def _build_obs_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard(
            "OBS WebSocket \u8fde\u63a5")
        form = QFormLayout()
        form.setSpacing(10)

        self.field_obs_host = QLineEdit("127.0.0.1")
        self.field_obs_port = QSpinBox()
        self.field_obs_port.setRange(1, 65535)
        self.field_obs_port.setValue(4455)
        self.field_obs_password = QLineEdit()
        self.field_obs_password.setEchoMode(
            QLineEdit.EchoMode.Password)
        self.field_obs_password.setPlaceholderText(
            "WebSocket \u5bc6\u7801 (\u53ef\u7a7a)")
        self.field_obs_auto_connect = QCheckBox(
            "\u542f\u52a8\u65f6\u81ea\u52a8\u8fde\u63a5")
        form.addRow(
            "\u5730\u5740:", self.field_obs_host)
        form.addRow(
            "\u7aef\u53e3:", self.field_obs_port)
        form.addRow(
            "\u5bc6\u7801:", self.field_obs_password)
        form.addRow(
            "", self.field_obs_auto_connect)
        card.addLayout(form)

        btn_row = QHBoxLayout()
        btn_auto = QPushButton(
            "\u81ea\u52a8\u8bc6\u522b\u7aef\u53e3")
        btn_auto.clicked.connect(
            self._auto_detect_obs_port)
        btn_row.addWidget(btn_auto)
        btn_test = QPushButton("\u6d4b\u8bd5\u8fde\u63a5")
        btn_test.clicked.connect(self._test_obs)
        btn_row.addWidget(btn_test)
        btn_row.addStretch()
        card.addLayout(btn_row)
        layout.addWidget(card)

        self._obs_status = QLabel("")
        self._obs_status.setStyleSheet(
            "font-size: 12px; color: #8b99b0; "
            "background: transparent;")
        layout.addWidget(self._obs_status)

        layout.addStretch()
        self.tabs.addWidget(page)

    def _auto_detect_obs_port(self):
        from core.hardware_detector import \
            HardwareDetector
        port = HardwareDetector.detect_obs_port()
        self.field_obs_port.setValue(port)
        QMessageBox.information(
            self, "\u8bc6\u522b\u7ed3\u679c",
            "OBS WebSocket \u7aef\u53e3: "
            + str(port))

    def _test_obs(self):
        try:
            from core.obs_controller import \
                OBSController
            test = OBSController()
            ok = test.connect(
                self.field_obs_host.text(),
                self.field_obs_port.value(),
                self.field_obs_password.text())
            if ok:
                self._obs_status.setText(
                    "\u2705 \u8fde\u63a5\u6210\u529f")
                self._obs_status.setStyleSheet(
                    "font-size: 12px; "
                    "color: #00e68a; "
                    "background: transparent;")
                test.disconnect()
            else:
                self._obs_status.setText(
                    "\u274c \u8fde\u63a5\u5931\u8d25")
                self._obs_status.setStyleSheet(
                    "font-size: 12px; "
                    "color: #ff3b5c; "
                    "background: transparent;")
        except Exception as e:
            self._obs_status.setText(
                "\u274c " + str(e)[:60])
            self._obs_status.setStyleSheet(
                "font-size: 12px; color: #ff3b5c; "
                "background: transparent;")

    # ═══════════════════════════════════════
    #  GSI tab
    # ═══════════════════════════════════════

    def _build_gsi_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard(
            "Game State Integration")
        form = QFormLayout()
        form.setSpacing(10)
        self.field_gsi_port = QSpinBox()
        self.field_gsi_port.setRange(1, 65535)
        self.field_gsi_port.setValue(3010)
        self.field_gsi_auto = QCheckBox(
            "\u542f\u52a8\u65f6\u81ea\u52a8\u5f00\u542f"
            " GSI \u670d\u52a1")
        form.addRow(
            "GSI \u7aef\u53e3:", self.field_gsi_port)
        form.addRow("", self.field_gsi_auto)
        card.addLayout(form)
        layout.addWidget(card)

        card2 = SettingsCard("CS2 \u8def\u5f84")
        cs2_row = QHBoxLayout()
        self.field_cs2_path = QLineEdit()
        self.field_cs2_path.setPlaceholderText(
            "CS2 \u5b89\u88c5\u76ee\u5f59 "
            "(\u53ef\u81ea\u52a8\u8bc6\u522b)")
        btn_cs2_auto = QPushButton(
            "\u81ea\u52a8\u8bc6\u522b")
        btn_cs2_auto.setFixedWidth(90)
        btn_cs2_auto.clicked.connect(
            self._auto_detect_cs2)
        btn_cs2_browse = QPushButton(
            "\u6d4f\u89c8")
        btn_cs2_browse.setFixedWidth(60)
        btn_cs2_browse.clicked.connect(
            self._browse_cs2)
        cs2_row.addWidget(self.field_cs2_path, 1)
        cs2_row.addWidget(btn_cs2_auto)
        cs2_row.addWidget(btn_cs2_browse)
        card2.addLayout(cs2_row)

        btn_install = QPushButton(
            "\u5b89\u88c5 GSI \u914d\u7f6e\u6587\u4ef6")
        btn_install.clicked.connect(
            self._install_gsi)
        card2.addWidget(btn_install)

        self._gsi_status = QLabel("")
        self._gsi_status.setStyleSheet(
            "font-size: 12px; color: #8b99b0; "
            "background: transparent;")
        card2.addWidget(self._gsi_status)
        layout.addWidget(card2)

        layout.addStretch()
        self.tabs.addWidget(page)

    def _auto_detect_cs2(self):
        from core.hardware_detector import \
            HardwareDetector
        cs2 = HardwareDetector.detect_cs2_path()
        if cs2:
            self.field_cs2_path.setText(cs2)
            QMessageBox.information(
                self, "\u8bc6\u522b\u6210\u529f",
                "CS2 \u8def\u5f84: " + cs2)
        else:
            QMessageBox.warning(
                self, "\u672a\u627e\u5230",
                "\u672a\u80fd\u81ea\u52a8\u8bc6\u522b"
                " CS2\n\u8bf7\u624b\u52a8\u6d4f\u89c8\u9009\u62e9")

    def _browse_cs2(self):
        path = QFileDialog.getExistingDirectory(
            self, "\u9009\u62e9 CS2 \u76ee\u5f59")
        if path:
            self.field_cs2_path.setText(path)

    def _install_gsi(self):
        path = self.field_cs2_path.text().strip()
        if not path:
            QMessageBox.warning(
                self, "\u63d0\u793a",
                "\u8bf7\u5148\u8bbe\u7f6e CS2 \u8def\u5f84"
                " (\u70b9\u51fb\u81ea\u52a8\u8bc6\u522b)")
            return
        try:
            from core.gsi_server import GSIServer
            gsi = GSIServer(
                self.settings,
                self.field_gsi_port.value())
            ok = gsi.install_gsi_config(path)
            if ok:
                self._gsi_status.setText(
                    "\u2705 \u5b89\u88c5\u6210\u529f"
                    "\uff0c\u8bf7\u91cd\u542f CS2")
                self._gsi_status.setStyleSheet(
                    "font-size: 12px; "
                    "color: #00e68a; "
                    "background: transparent;")
            else:
                self._gsi_status.setText(
                    "\u274c \u672a\u627e\u5230 "
                    "CS2 cfg \u76ee\u5f59")
                self._gsi_status.setStyleSheet(
                    "font-size: 12px; "
                    "color: #ff3b5c; "
                    "background: transparent;")
        except Exception as e:
            QMessageBox.critical(
                self, "\u9519\u8bef", str(e))

    # ═══════════════════════════════════════
    #  Detection tab
    # ═══════════════════════════════════════

    def _build_detection_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard(
            "\u9ad8\u5149\u7247\u68c0\u6d4b\u53c2\u6570")
        form = QFormLayout()
        form.setSpacing(10)
        self.field_min_score = QSpinBox()
        self.field_min_score.setRange(0, 100)
        self.field_min_score.setValue(3)
        form.addRow(
            "\u6700\u4f4e\u5206\u6570:",
            self.field_min_score)

        self.field_min_kills = QSpinBox()
        self.field_min_kills.setRange(1, 5)
        self.field_min_kills.setValue(2)
        form.addRow(
            "\u8fde\u6740\u6700\u5c11\u6740:",
            self.field_min_kills)

        self.field_clutch_kills = QSpinBox()
        self.field_clutch_kills.setRange(1, 5)
        self.field_clutch_kills.setValue(2)
        form.addRow(
            "Clutch \u6700\u5c11\u6740:",
            self.field_clutch_kills)

        self.field_before_buffer = QSpinBox()
        self.field_before_buffer.setRange(1, 10)
        self.field_before_buffer.setValue(3)
        form.addRow(
            "\u7247\u6bb5\u524d\u7f00:",
            self.field_before_buffer)

        self.field_after_buffer = QSpinBox()
        self.field_after_buffer.setRange(1, 10)
        self.field_after_buffer.setValue(5)
        form.addRow(
            "\u7247\u6bb5\u540e\u7f00:",
            self.field_after_buffer)
        card.addLayout(form)
        layout.addWidget(card)

        card2 = SettingsCard("Demo \u6587\u4ef6\u5939")
        demo_row = QHBoxLayout()
        self.field_demo_folder = QLineEdit()
        self.field_demo_folder.setPlaceholderText(
            "Demo \u5b58\u653e\u76ee\u5f59 "
            "(\u53ef\u81ea\u52a8\u8bc6\u522b)")
        btn_demo_auto = QPushButton(
            "\u81ea\u52a8\u8bc6\u522b")
        btn_demo_auto.setFixedWidth(90)
        btn_demo_auto.clicked.connect(
            self._auto_detect_demo)
        btn_demo = QPushButton("\u6d4f\u89c8")
        btn_demo.setFixedWidth(60)
        btn_demo.clicked.connect(self._browse_demo)
        demo_row.addWidget(
            self.field_demo_folder, 1)
        demo_row.addWidget(btn_demo_auto)
        demo_row.addWidget(btn_demo)
        card2.addLayout(demo_row)
        layout.addWidget(card2)

        layout.addStretch()
        self.tabs.addWidget(page)

    def _auto_detect_demo(self):
        from core.hardware_detector import \
            HardwareDetector
        path = HardwareDetector.detect_demo_folder()
        if path:
            self.field_demo_folder.setText(path)
            QMessageBox.information(
                self, "\u8bc6\u522b\u6210\u529f",
                "Demo \u76ee\u5f59: " + path)
        else:
            QMessageBox.warning(
                self, "\u672a\u627e\u5230",
                "\u672a\u627e\u5230 CS2 "
                "Demo \u76ee\u5f59\n"
                "\u8bf7\u624b\u52a8\u6d4f\u89c8\u9009\u62e9")

    def _browse_demo(self):
        path = QFileDialog.getExistingDirectory(
            self, "\u9009\u62e9 Demo \u76ee\u5f59")
        if path:
            self.field_demo_folder.setText(path)

    # ═══════════════════════════════════════
    #  Output tab
    # ═══════════════════════════════════════

    def _build_output_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard("\u8f93\u51fa\u8bbe\u7f6e")
        form = QFormLayout()
        form.setSpacing(10)

        out_row = QHBoxLayout()
        self.field_output_dir = QLineEdit()
        self.field_output_dir.setPlaceholderText(
            "\u96c6\u9526\u8f93\u51fa\u76ee\u5f59")
        btn_out = QPushButton("\u6d4f\u89c8")
        btn_out.clicked.connect(self._browse_output)
        out_row.addWidget(
            self.field_output_dir, 1)
        out_row.addWidget(btn_out)
        form.addRow(
            "\u8f93\u51fa\u76ee\u5f59:", out_row)

        self.field_output_quality = QComboBox()
        self.field_output_quality.addItems([
            "\u753b\u8d28\u4f18\u5148 "
            "(\u63a8\u8350)",
            "\u5747\u8861\u6a21\u5f0f",
            "\u901f\u5ea6\u4f18\u5148",
            "\u590d\u5236\u6a21\u5f0f "
            "(\u65e0\u635f\u5feb\u901f)"])
        form.addRow(
            "\u753b\u8d28:",
            self.field_output_quality)

        self.field_output_format = QComboBox()
        self.field_output_format.addItems(
            ["mp4", "mkv", "mov"])
        form.addRow(
            "\u5c01\u88c5\u683c\u5f0f:",
            self.field_output_format)
        card.addLayout(form)
        layout.addWidget(card)

        card2 = SettingsCard("FFmpeg")
        ff_row = QHBoxLayout()
        self.field_ffmpeg = QLineEdit()
        self.field_ffmpeg.setPlaceholderText(
            "ffmpeg \u8def\u5f84 "
            "(\u53ef\u81ea\u52a8\u8bc6\u522b)")
        btn_ffmpeg_auto = QPushButton(
            "\u81ea\u52a8\u8bc6\u522b")
        btn_ffmpeg_auto.setFixedWidth(90)
        btn_ffmpeg_auto.clicked.connect(
            self._auto_detect_ffmpeg)
        btn_ffmpeg = QPushButton("\u6d4f\u89c8")
        btn_ffmpeg.setFixedWidth(60)
        btn_ffmpeg.clicked.connect(
            self._browse_ffmpeg)
        ff_row.addWidget(self.field_ffmpeg, 1)
        ff_row.addWidget(btn_ffmpeg_auto)
        ff_row.addWidget(btn_ffmpeg)
        card2.addLayout(ff_row)
        layout.addWidget(card2)

        layout.addStretch()
        self.tabs.addWidget(page)

    def _auto_detect_ffmpeg(self):
        from core.hardware_detector import \
            HardwareDetector
        path = HardwareDetector.detect_ffmpeg()
        if path:
            self.field_ffmpeg.setText(path)
            QMessageBox.information(
                self, "\u8bc6\u522b\u6210\u529f",
                "FFmpeg: " + path)
        else:
            QMessageBox.warning(
                self, "\u672a\u627e\u5230",
                "\u672a\u627e\u5230 FFmpeg\n"
                "\u8bf7\u5b89\u88c5 FFmpeg "
                "\u6216\u624b\u52a8\u6307\u5b9a\u8def\u5f84")

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "\u9009\u62e9\u8f93\u51fa\u76ee\u5f59")
        if path:
            self.field_output_dir.setText(path)

    def _browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "\u9009\u62e9 ffmpeg")
        if path:
            self.field_ffmpeg.setText(path)

    # ═══════════════════════════════════════
    #  Advanced tab
    # ═══════════════════════════════════════

    def _build_advanced_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard("\u70ed\u952e\u8bbe\u7f6e")
        hk_row = QHBoxLayout()
        hk_row.setSpacing(20)

        hk1 = QVBoxLayout()
        hk1.addWidget(QLabel(
            "\u5f00\u59cb/\u505c\u6b62\u5f55\u5236"))
        self.field_hk_record = QLineEdit("F9")
        self.field_hk_record.setMaximumWidth(100)
        hk1.addWidget(self.field_hk_record)
        hk_row.addLayout(hk1)

        hk2 = QVBoxLayout()
        hk2.addWidget(QLabel(
            "Replay Buffer \u4fdd\u5b58"))
        self.field_hk_replay = QLineEdit("F10")
        self.field_hk_replay.setMaximumWidth(100)
        hk2.addWidget(self.field_hk_replay)
        hk_row.addLayout(hk2)

        hk_row.addStretch()
        card.addLayout(hk_row)
        layout.addWidget(card)

        layout.addStretch()
        self.tabs.addWidget(page)

    # ═══════════════════════════════════════
    #  About / Update tab
    # ═══════════════════════════════════════

    def _build_about_tab(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = SettingsCard("\u5173\u4e8e")
        from core.updater import CURRENT_VERSION
        ver_row = QHBoxLayout()
        ver_lbl = QLabel(
            "\u5f53\u524d\u7248\u672c:  v"
            + CURRENT_VERSION)
        ver_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 700; "
            "color: #e8edf5; "
            "background: transparent;")
        ver_row.addWidget(ver_lbl)
        ver_row.addStretch()
        card.addLayout(ver_row)

        gh_row = QHBoxLayout()
        gh_lbl = QLabel(
            "\u2014 CS2 Highlight Studio \u00b7 "
            "MIT License")
        gh_lbl.setStyleSheet(
            "font-size: 12px; color: #4a5c78; "
            "background: transparent;")
        gh_row.addWidget(gh_lbl)
        gh_row.addStretch()
        card.addLayout(gh_row)

        self._update_status = QLabel("")
        self._update_status.setStyleSheet(
            "font-size: 13px; color: #8b99b0; "
            "background: transparent;")
        card.addWidget(self._update_status)

        layout.addWidget(card)

        card2 = SettingsCard("\u66f4\u65b0")
        self._chk_auto = QCheckBox(
            "\u542f\u52a8\u65f6\u81ea\u52a8"
            "\u68c0\u67e5\u66f4\u65b0")
        self._chk_notify = QCheckBox(
            "\u6709\u65b0\u7248\u672c\u65f6"
            "\u5f39\u7a97\u63d0\u793a")
        self._chk_auto_dl = QCheckBox(
            "\u6709\u65b0\u7248\u672c\u65f6"
            "\u81ea\u52a8\u4e0b\u8f7d")
        card2.addWidget(self._chk_auto)
        card2.addWidget(self._chk_notify)
        card2.addWidget(self._chk_auto_dl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_check = QPushButton(
            "\u7acb\u5373\u68c0\u67e5\u66f4\u65b0")
        self._btn_check.setFixedHeight(36)
        self._btn_check.setStyleSheet(
            "QPushButton { background: #1a2744; "
            "color: #e8edf5; "
            "border: 1px solid #2a3a5c; "
            "border-radius: 8px; "
            "padding: 0 16px; "
            "font-size: 13px; }"
            "QPushButton:hover { "
            "background: #223050; }")
        self._btn_check.clicked.connect(
            self._check_update)
        btn_row.addWidget(self._btn_check)

        self._btn_download = QPushButton(
            "\u4e0b\u8f7d\u66f4\u65b0")
        self._btn_download.setFixedHeight(36)
        self._btn_download.setVisible(False)
        self._btn_download.setStyleSheet(
            "QPushButton { background: #00b4ff; "
            "color: #080c14; font-weight: 700; "
            "border: none; border-radius: 8px; "
            "padding: 0 16px; "
            "font-size: 13px; }"
            "QPushButton:hover { "
            "background: #00c8ff; }")
        self._btn_download.clicked.connect(
            self._download_update)
        btn_row.addWidget(self._btn_download)

        btn_row.addStretch()
        card2.addLayout(btn_row)
        layout.addWidget(card2)
        
        # ── Language ──
        card_lang = SettingsCard(t("lang_title"))
        lang_row = QHBoxLayout()
        lang_row.setSpacing(12)

        lang_lbl = QLabel(t("lang_label"))
        lang_lbl.setStyleSheet(
            "font-size: 13px; color: #e8edf5; "
            "background: transparent;")
        lang_row.addWidget(lang_lbl)

        self._lang_combo = QComboBox()
        self._lang_combo.setFixedWidth(120)
        self._lang_combo.addItem(t("lang_zh"), "zh")
        self._lang_combo.addItem(t("lang_en"), "en")
        lang_row.addWidget(self._lang_combo)

        lang_hint = QLabel(t("lang_restart"))
        lang_hint.setStyleSheet(
            "font-size: 11px; color: #4a5c78; "
            "background: transparent;")
        lang_row.addWidget(lang_hint)
        lang_row.addStretch()
        card_lang.addLayout(lang_row)
        layout.addWidget(card_lang)
        
        # ── Clean data ──
        card3 = SettingsCard(
            "\u6570\u636e\u7ba1\u7406")
        warn = QLabel(
            "\u6e05\u9664\u5c06\u5220\u9664\u6240\u6709"
            "\u5bf9\u5c40\u8bb0\u5f55\u3001\u7f13\u5b58"
            "\u548c\u8bbe\u7f6e\uff0c\u6b64\u64cd\u4f5c"
            "\u4e0d\u53ef\u64a4\u9500")
        warn.setStyleSheet(
            "font-size: 12px; color: #ff9f43; "
            "background: transparent;")
        card3.addWidget(warn)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)

        btn_cache = QPushButton(
            "\u6e05\u9664\u7f13\u5b58")
        btn_cache.setObjectName("dangerBtn")
        btn_cache.setFixedHeight(36)
        btn_cache.clicked.connect(
            self._clean_cache)
        btn_row2.addWidget(btn_cache)

        btn_all = QPushButton(
            "\u6e05\u9664\u6240\u6709\u6570\u636e")
        btn_all.setObjectName("dangerBtn")
        btn_all.setFixedHeight(36)
        btn_all.setStyleSheet(
            "QPushButton { background: #ff3b5c; "
            "color: #ffffff; border: none; "
            "border-radius: 8px; padding: 0 16px; "
            "font-size: 13px; font-weight: 700; }"
            "QPushButton:hover { "
            "background: #ff5577; }")
        btn_all.clicked.connect(
            self._clean_all_data)
        btn_row2.addWidget(btn_all)

        btn_row2.addStretch()
        card3.addLayout(btn_row2)

        self._clean_status = QLabel("")
        self._clean_status.setStyleSheet(
            "font-size: 12px; color: #00e68a; "
            "background: transparent;")
        card3.addWidget(self._clean_status)

        layout.addWidget(card3)

        layout.addStretch()
        self.tabs.addWidget(page)

    # ═══════════════════════════════════════
    #  Update logic
    # ═══════════════════════════════════════

    def _check_update(self):
        from core.updater import (
            check_for_update, CURRENT_VERSION)
        self._btn_check.setEnabled(False)
        self._btn_check.setText(
            "\u68c0\u67e5\u4e2d...")
        self._update_status.setText(
            "\u6b63\u5728\u8fde\u63a5 GitHub...")
        self._update_status.setStyleSheet(
            "font-size: 13px; color: #8b99b0; "
            "background: transparent;")

        self._update_thread = _UpdateThread()
        self._update_thread.result.connect(
            self._on_update_result)
        self._update_thread.start()

    def _on_update_result(self, info):
        from core.updater import CURRENT_VERSION
        self._btn_check.setEnabled(True)
        self._btn_check.setText(
            "\u7acb\u5373\u68c0\u67e5\u66f4\u65b0")
        self._btn_download.setVisible(False)

        if info.error:
            self._update_status.setText(
                "\u274c " + info.error)
            self._update_status.setStyleSheet(
                "font-size: 13px; color: #ff3b5c; "
                "background: transparent;")
            return

        if info.has_update:
            self._update_status.setText(
                "\u2191 \u6709\u65b0\u7248\u672c: "
                "v{} (\u5f53\u524d v{})".format(
                    info.latest, CURRENT_VERSION))
            self._update_status.setStyleSheet(
                "font-size: 13px; color: #00e68a; "
                "font-weight: 600; "
                "background: transparent;")
            self._btn_download.setVisible(True)
            self._latest_url = info.download_url

            if (self.settings
                    and self.settings.get(
                        "update_notify", True)):
                from PyQt6.QtWidgets import (
                    QMessageBox as MB)
                msg = MB(self)
                msg.setIcon(MB.Icon.Information)
                msg.setWindowTitle(
                    "\u6709\u65b0\u7248\u672c\u53ef\u7528")
                msg.setText(
                    "\u53d1\u73b0\u65b0\u7248\u672c "
                    "v{} \u2192 v{}".format(
                        CURRENT_VERSION,
                        info.latest))
                notes = info.release_notes
                if notes:
                    msg.setInformativeText(
                        "\u66f4\u65b0\u5185\u5bb9:\n"
                        + notes)
                msg.setStandardButtons(
                    MB.StandardButton.Ok
                    | MB.StandardButton.Cancel)
                if (msg.exec()
                        == MB.StandardButton.Ok):
                    self._download_update()
        else:
            self._update_status.setText(
                "\u2705 \u5df2\u662f\u6700\u65b0"
                "\u7248\u672c v" + CURRENT_VERSION)
            self._update_status.setStyleSheet(
                "font-size: 13px; color: #00e68a; "
                "background: transparent;")

    def _download_update(self):
        from core.updater import (
            download_update, open_release_page)
        url = getattr(
            self, "_latest_url", "")
        if not url:
            open_release_page()
            return

        self._btn_download.setEnabled(False)
        self._btn_download.setText(
            "\u4e0b\u8f7d\u4e2d...")
        self._update_status.setText(
            "\u6b63\u5728\u4e0b\u8f7d...")

        dest = ""
        if self.settings:
            dest = self.settings.get(
                "output_dir", "")
        if not dest:
            dest = os.path.expanduser(
                "~\\Downloads")

        self._dl_thread = _DownloadThread(
            url, dest)
        self._dl_thread.done.connect(
            self._on_download_done)
        self._dl_thread.start()

    def _on_download_done(self, path):
        self._btn_download.setEnabled(True)
        self._btn_download.setText(
            "\u4e0b\u8f7d\u66f4\u65b0")

        if path:
            from core.updater import \
                launch_installer
            self._update_status.setText(
                "\u2705 \u4e0b\u8f7d\u5b8c\u6210"
                "\uff0c\u6b63\u5728\u542f\u52a8"
                "\u5b89\u88c5...")
            launch_installer(path)
        else:
            from core.updater import \
                open_release_page
            self._update_status.setText(
                "\u274c \u4e0b\u8f7d\u5931\u8d25"
                "\uff0c\u5df2\u6253\u5f00\u7f51\u9875")
            open_release_page()

    def check_update_on_start(self):
        """Called from MainWindow on startup."""
        if not self.settings:
            return
        if not self.settings.get(
                "update_auto_check", True):
            return
        self._startup_checker = _UpdateThread()
        self._startup_checker.result.connect(
            self._on_startup_check)
        self._startup_checker.start()

    def _on_startup_check(self, info):
        if not info.has_update:
            return
        if not self.settings:
            return
        if not self.settings.get(
                "update_notify", True):
            return

        from core.updater import (
            CURRENT_VERSION, open_release_page)
        from PyQt6.QtWidgets import (
            QMessageBox as MB)
        msg = MB(self)
        msg.setIcon(MB.Icon.Information)
        msg.setWindowTitle(
            "\u6709\u65b0\u7248\u672c\u53ef\u7528")
        msg.setText(
            "\u53d1\u73b0\u65b0\u7248\u672c "
            "v{} \u2192 v{}".format(
                CURRENT_VERSION, info.latest))
        notes = info.release_notes
        if notes:
            msg.setInformativeText(
                "\u66f4\u65b0\u5185\u5bb9:\n" + notes)
        msg.setStandardButtons(
            MB.StandardButton.Ok
            | MB.StandardButton.Cancel)
        if msg.exec() == MB.StandardButton.Ok:
            self._latest_url = info.download_url
            self._download_update()

    # ═══════════════════════════════════════
    #  Init / Load / Save
    # ═══════════════════════════════════════

    def _init_fields(self):
        if not self.settings:
            return
        s = self.settings

        self.field_steam_id.setText(
            s.get("steam_id", ""))
        tr_val = s.get("tick_rate", 64)
        tr = "Auto" if tr_val == 0 else str(tr_val)
        idx = self.field_tick_rate.findText(tr)
        if idx >= 0:
            self.field_tick_rate.setCurrentIndex(idx)
        self.field_auto_record.setChecked(
            s.get(
                "auto_record_on_match_start", False))
        self.field_auto_process.setChecked(
            s.get("auto_process_new_demo", True))
        self.field_hotkeys.setChecked(
            s.get("hotkeys_enabled", False))

        self.field_obs_host.setText(
            s.get("obs_host", "127.0.0.1"))
        self.field_obs_port.setValue(
            int(s.get("obs_port", 4455)))
        self.field_obs_password.setText(
            s.get("obs_password", ""))
        self.field_obs_auto_connect.setChecked(
            s.get("obs_auto_connect", True))

        self.field_gsi_port.setValue(
            int(s.get("gsi_port", 3010)))
        self.field_gsi_auto.setChecked(
            s.get("gsi_auto_start", True))
        self.field_cs2_path.setText(
            s.get("cs2_install_path", ""))

        self.field_min_score.setValue(
            int(s.get("min_highlight_score", 3)))
        self.field_min_kills.setValue(
            int(s.get(
                "min_consecutive_kills", 2)))
        self.field_clutch_kills.setValue(
            int(s.get("min_clutch_kills", 2)))
        self.field_before_buffer.setValue(
            int(s.get(
                "before_buffer_seconds", 3)))
        self.field_after_buffer.setValue(
            int(s.get(
                "after_buffer_seconds", 5)))
        self.field_demo_folder.setText(
            s.get("demo_folder", ""))

        self.field_output_dir.setText(
            s.get("output_dir", ""))
        q = s.get("output_quality", "balanced")
        q_map = {
            "quality": 0, "balanced": 1,
            "speed": 2, "copy": 3,
            "very_high": 0, "high": 1,
            "medium": 1, "low": 2}
        self.field_output_quality.setCurrentIndex(
            q_map.get(q, 1))
        fmt = s.get("output_format", "mp4")
        fi = self.field_output_format.findText(fmt)
        if fi >= 0:
            self.field_output_format.setCurrentIndex(
                fi)
        self.field_ffmpeg.setText(
            s.get("ffmpeg_path", ""))
        self.field_hk_record.setText(
            s.get("hotkey_record", "F9"))
        self.field_hk_replay.setText(
            s.get("hotkey_replay", "F10"))

        self._chk_auto.setChecked(
            s.get("update_auto_check", True))
        self._chk_notify.setChecked(
            s.get("update_notify", True))
        self._chk_auto_dl.setChecked(
            s.get("update_auto_download", False))
        
        lang = s.get("language", "zh")
        idx = self._lang_combo.findData(lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)


    def _on_save(self):
        if not self.settings:
            return
        s = self.settings

        s.set("steam_id",
              self.field_steam_id.text().strip())
        tr_text = self.field_tick_rate.currentText()
        s.set("tick_rate",
              0 if tr_text == "Auto"
              else int(tr_text))
        s.set("auto_record_on_match_start",
              self.field_auto_record.isChecked())
        s.set("auto_process_new_demo",
              self.field_auto_process.isChecked())
        s.set("hotkeys_enabled",
              self.field_hotkeys.isChecked())

        s.set("obs_host",
              self.field_obs_host.text().strip())
        s.set("obs_port",
              self.field_obs_port.value())
        s.set("obs_password",
              self.field_obs_password.text())
        s.set("obs_auto_connect",
              self.field_obs_auto_connect.isChecked())

        s.set("gsi_port",
              self.field_gsi_port.value())
        s.set("gsi_auto_start",
              self.field_gsi_auto.isChecked())
        s.set("cs2_install_path",
              self.field_cs2_path.text().strip())

        s.set("min_highlight_score",
              self.field_min_score.value())
        s.set("min_consecutive_kills",
              self.field_min_kills.value())
        s.set("min_clutch_kills",
              self.field_clutch_kills.value())
        s.set("before_buffer_seconds",
              self.field_before_buffer.value())
        s.set("after_buffer_seconds",
              self.field_after_buffer.value())
        s.set("demo_folder",
              self.field_demo_folder.text().strip())

        s.set("output_dir",
              self.field_output_dir.text().strip())
        q_text = \
            self.field_output_quality.currentText()
        if "\u753b\u8d28" in q_text:
            q_val = "quality"
        elif "\u901f\u5ea6" in q_text:
            q_val = "speed"
        elif "\u590d\u5236" in q_text:
            q_val = "copy"
        else:
            q_val = "balanced"
        s.set("output_quality", q_val)
        s.set("output_format",
              self.field_output_format.currentText())
        s.set("ffmpeg_path",
              self.field_ffmpeg.text().strip())

        s.set("hotkey_record",
              self.field_hk_record.text().strip()
              or "F9")
        s.set("hotkey_replay",
              self.field_hk_replay.text().strip()
              or "F10")

        s.set("update_auto_check",
              self._chk_auto.isChecked())
        s.set("update_notify",
              self._chk_notify.isChecked())
        s.set("update_auto_download",
              self._chk_auto_dl.isChecked())
        s.set("language",
              self._lang_combo.currentData())

        s.save()

        self._btn_save.setText(
            "\u2713 \u5df2\u4fdd\u5b58")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500,
            lambda: self._btn_save.setText(
                "\u4fdd\u5b58\u8bbe\u7f6e"))
        
    # ═══════════════════════════════════════
    #  Clean data
    # ═══════════════════════════════════════

    def _clean_cache(self):
        from PyQt6.QtWidgets import QMessageBox
        ret = QMessageBox.warning(
            self, "清除缓存",
            "确定要清除所有缓存数据吗？\n\n"
            "包括：\n"
            "• Demo 解析缓存\n"
            "• 对局记录文件\n"
            "• 时间戳缓存\n\n"
            "不会删除设置文件",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return

        import shutil
        count = 0
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", ".."))

        # config_data folder (match_history etc)
        data_dir = os.path.join(
            project_root, "config_data")
        if os.path.isdir(data_dir):
            for f in os.listdir(data_dir):
                fp = os.path.join(data_dir, f)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        count += 1
                except Exception:
                    pass

        # Also check legacy "data" folder
        data_dir2 = os.path.join(
            project_root, "data")
        if os.path.isdir(data_dir2):
            for f in os.listdir(data_dir2):
                fp = os.path.join(data_dir2, f)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        count += 1
                except Exception:
                    pass

        # Demo parse cache
        cache_dir = os.path.join(
            project_root, "cache")
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                fp = os.path.join(cache_dir, f)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        count += 1
                    elif os.path.isdir(fp):
                        shutil.rmtree(fp)
                        count += 1
                except Exception:
                    pass

        self._clean_status.setText(
            "缓存已清除，删除 {} 个文件".format(
                count))

    def _clean_all_data(self):
        from PyQt6.QtWidgets import QMessageBox
        ret = QMessageBox.critical(
            self, "\u2757 \u6e05\u9664\u6240\u6709\u6570\u636e",
            "\u786e\u5b9a\u8981\u5220\u9664\u6240\u6709"
            "\u6570\u636e\u5417\uff1f\n\n"
            "\u5c06\u5220\u9664\uff1a\n"
            "\u2022 \u6240\u6709\u5bf9\u5c40\u8bb0\u5f55\n"
            "\u2022 \u6240\u6709\u7f13\u5b58\u6587\u4ef6\n"
            "\u2022 \u6240\u6709\u89c6\u9891\u8f93\u51fa\u6587\u4ef6\n"
            "\u2022 \u6240\u6709\u81ea\u5b9a\u4e49\u8bbe\u7f6e\n\n"
            "\u203b \u6b64\u64cd\u4f5c\u5b8c\u5168\u4e0d\u53ef\u64a4\u9500\uff01",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return

        import shutil
        count = 0
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", ".."))


        # Folders to clean
        clean_dirs = ["data", "cache", "logs",
                      "output", "temp"]
        for d in clean_dirs:
            dp = os.path.join(project_root, d)
            if os.path.isdir(dp):
                for f in os.listdir(dp):
                    fp = os.path.join(dp, f)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                            count += 1
                        elif os.path.isdir(fp):
                            shutil.rmtree(fp)
                            count += 1
                    except Exception:
                        pass

        # Settings files (keep structure, reset)
        settings_files = []
        cfg_dir = os.path.join(project_root, "config")
        if os.path.isdir(cfg_dir):
            for f in os.listdir(cfg_dir):
                if f.endswith(".json"):
                    settings_files.append(
                        os.path.join(cfg_dir, f))

        for sf in settings_files:
            try:
                os.remove(sf)
                count += 1
            except Exception:
                pass

        self._clean_status.setText(
            "\u2705 \u5168\u90e8\u6570\u636e\u5df2\u6e05\u9664"
            "\uff0c\u5220\u9664 {} \u4e2a\u6587\u4ef6"
            "\u2014\u2014 \u8bf7\u91cd\u542f\u7a0b\u5e8f".format(
                count))

        self._clean_status.setStyleSheet(
            "font-size: 12px; color: #ff9f43; "
            "font-weight: 700; "
            "background: transparent;")

    # ═══════════════════════════════════════
    #  Auto-config dialog
    # ═══════════════════════════════════════

    def _open_auto_config(self):
        from ui.widgets.obs_auto_config_dialog \
            import OBSAutoConfigDialog
        obs = self._obs_controller
        if obs is None:
            QMessageBox.information(
                self, "\u63d0\u793a",
                "\u8bf7\u786e\u4fdd\u5df2\u8fde\u63a5"
                " OBS WebSocket")
            return
        dlg = OBSAutoConfigDialog(obs, self)
        dlg.exec()


# ═══════════════════════════════════════
#  Background threads
# ═══════════════════════════════════════

class _UpdateThread(QThread):
    result = pyqtSignal(object)

    def run(self):
        from core.updater import check_for_update
        info = check_for_update()
        self.result.emit(info)


class _DownloadThread(QThread):
    done = pyqtSignal(str)

    def __init__(self, url, dest):
        super().__init__()
        self._url = url
        self._dest = dest

    def run(self):
        from core.updater import download_update
        path = download_update(
            self._url, self._dest)
        self.done.emit(path or "")
