"""
Dashboard page
"""
import os
import sys
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ui.widgets.status_card import StatusCard
from ui.widgets.glow_button import GlowButton

_FLAGS = 0
if sys.platform == "win32":
    _FLAGS = getattr(
        subprocess, "CREATE_NO_WINDOW", 0)


class _FFmpegChecker(QThread):
    done = pyqtSignal(bool)

    def run(self):
        try:
            r = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, timeout=5,
                creationflags=_FLAGS)
            self.done.emit(r.returncode == 0)
        except Exception:
            self.done.emit(False)


class _ObsChecker(QThread):
    done = pyqtSignal(bool, bool)

    def __init__(self, obs):
        super().__init__()
        self._obs = obs

    def run(self):
        c, r = False, False
        try:
            if self._obs:
                self._obs._update_state()
                c = self._obs.state.connected
                r = self._obs.state.recording
        except Exception:
            pass
        self.done.emit(c, r)


class _GsiChecker(QThread):
    done = pyqtSignal(bool, bool)

    def __init__(self, gsi):
        super().__init__()
        self._gsi = gsi

    def run(self):
        rx, c = False, False
        try:
            if self._gsi:
                rx = self._gsi.is_gsi_receiving()
                c = self._gsi.state.connected
        except Exception:
            pass
        self.done.emit(rx, c)


class DashboardPage(QWidget):

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._obs = None
        self._gsi = None
        self._setup_ui()
        self._connect_clicks()

    def set_controllers(self, obs, gsi):
        self._obs = obs
        self._gsi = gsi

    def _connect_clicks(self):
        self.obs_card.installEventFilter(self)
        self.gsi_card.installEventFilter(self)
        self.ffmpeg_card.installEventFilter(self)

        for card in (self.obs_card,
                     self.gsi_card,
                     self.ffmpeg_card):
            card.setCursor(
                Qt.CursorShape.PointingHandCursor)

    def eventFilter(self, obj, event):
        if (event.type()
                == event.Type.MouseButtonRelease):
            if obj is self.obs_card:
                self._refresh_obs()
                return True
            if obj is self.gsi_card:
                self._refresh_gsi()
                return True
            if obj is self.ffmpeg_card:
                self._refresh_ffmpeg()
                return True
        return super().eventFilter(obj, event)

    def _refresh_obs(self):
        self.obs_card.set_value(
            "检测中...", "#ff9f43")
        t = _ObsChecker(self._obs)
        t.done.connect(self._on_obs_done)
        t.start()
        self._t_obs = t

    def _on_obs_done(self, connected, recording):
        if connected:
            if recording:
                self.obs_card.set_value(
                    "录制中", "#ff3b5c")
            else:
                self.obs_card.set_value(
                    "已连接(空闲)", "#00e68a")
        else:
            self.obs_card.set_value(
                "未连接", "#ff3b5c")

    def _refresh_gsi(self):
        self.gsi_card.set_value(
            "检测中...", "#ff9f43")
        t = _GsiChecker(self._gsi)
        t.done.connect(self._on_gsi_done)
        t.start()
        self._t_gsi = t

    def _on_gsi_done(self, receiving, connected):
        if receiving:
            self.gsi_card.set_value(
                "接收中", "#00e68a")
        elif connected:
            self.gsi_card.set_value(
                "等待数据", "#ff9f43")
        else:
            self.gsi_card.set_value(
                "未启动", "#ff3b5c")

    def _refresh_ffmpeg(self):
        self.ffmpeg_card.set_value(
            "检测中...", "#ff9f43")
        t = _FFmpegChecker()
        t.done.connect(self._on_ffmpeg_done)
        t.start()
        self._t_ff = t

    def _on_ffmpeg_done(self, ok):
        if ok:
            self.ffmpeg_card.set_value(
                "就绪", "#00e68a")
            return
        try:
            p = self.window()
            if p and hasattr(p, 'settings'):
                path = p.settings.get(
                    "ffmpeg_path", "")
                if path and os.path.isfile(path):
                    self.ffmpeg_card.set_value(
                        "就绪", "#00e68a")
                    return
        except Exception:
            pass
        self.ffmpeg_card.set_value(
            "未安装", "#ff3b5c")

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "background: transparent;")

        container = QWidget()
        container.setStyleSheet(
            "background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        title = QLabel("仪表盘")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        subtitle = QLabel(
            "CS2 高光自动剪辑工作台总览")
        subtitle.setObjectName("subheading")
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.obs_card = StatusCard(
            title="OBS STUDIO",
            value="未连接",
            subtitle="通过 WebSocket 控制录制",
            accent_color="#ff3b5c",
            icon="●")

        self.gsi_card = StatusCard(
            title="GSI SERVER",
            value="未启动",
            subtitle="监听 CS2 游戏状态",
            accent_color="#00b4ff",
            icon="▶")

        self.ffmpeg_card = StatusCard(
            title="FFMPEG",
            value="检测中...",
            subtitle="视频裁剪与拼接引擎",
            accent_color="#ff9f43",
            icon="◆")

        self.highlights_card = StatusCard(
            title="高光片段",
            value="0",
            subtitle="等待解析 Demo 文件",
            accent_color="#8b5cf6",
            icon="★")

        cards_layout.addWidget(self.obs_card)
        cards_layout.addWidget(self.gsi_card)
        cards_layout.addWidget(self.ffmpeg_card)
        cards_layout.addWidget(
            self.highlights_card)
        layout.addLayout(cards_layout)

        hint = QLabel(
            "ℹ 点击状态卡片可刷新检测")
        hint.setStyleSheet(
            "font-size: 11px; color: #4a5c78; "
            "background: transparent;")
        layout.addWidget(hint)

        # Quick actions
        ag = QFrame()
        ag.setStyleSheet("""
            QFrame { background: #111a2e;
            border: 1px solid #1a2744;
            border-radius: 12px; }
        """)
        al = QVBoxLayout(ag)
        al.setContentsMargins(24, 20, 24, 20)
        al.setSpacing(16)

        at = QLabel("快速操作")
        at.setStyleSheet("""
            font-family: "Exo 2"; font-size: 15px;
            font-weight: 600; color: #e8edf5;
            background: transparent;
        """)
        al.addWidget(at)

        br = QHBoxLayout()
        br.setSpacing(12)
        self.btn_parse = GlowButton(
            "\U0001f4c2  选择 Demo 解析")
        self.btn_scan = GlowButton(
            "\U0001f50d  扫描 Demo 文件夹",
            color="#8b5cf6")
        self.btn_output = GlowButton(
            "\U0001f4c1  打开输出目录",
            color="#00e68a")
        br.addWidget(self.btn_parse)
        br.addWidget(self.btn_scan)
        br.addWidget(self.btn_output)
        br.addStretch()
        al.addLayout(br)
        layout.addWidget(ag)

        # Info area
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        rf = QFrame()
        rf.setStyleSheet("""
            QFrame { background: #111a2e;
            border: 1px solid #1a2744;
            border-radius: 12px; }
        """)
        rl = QVBoxLayout(rf)
        rl.setContentsMargins(20, 16, 20, 16)
        rl.setSpacing(10)
        rt = QLabel("最近活动")
        rt.setStyleSheet("""
            font-family: "Exo 2"; font-size: 14px;
            font-weight: 600; color: #8b99b0;
            background: transparent;
        """)
        rl.addWidget(rt)
        self.recent_list = QLabel(
            "暂无活动记录\n\n"
            "解析 Demo 或等待 GSI 检测"
            "对局结束后自动处理")
        self.recent_list.setWordWrap(True)
        self.recent_list.setStyleSheet(
            "font-size: 13px; color: #4a5c78; "
            "background: transparent; "
            "padding: 20px;")
        rl.addWidget(self.recent_list)
        rl.addStretch()
        info_layout.addWidget(rf)

        gf = QFrame()
        gf.setStyleSheet("""
            QFrame { background: #111a2e;
            border: 1px solid #1a2744;
            border-radius: 12px; }
        """)
        gl = QVBoxLayout(gf)
        gl.setContentsMargins(20, 16, 20, 16)
        gl.setSpacing(10)
        gt = QLabel("使用指南")
        gt.setStyleSheet("""
            font-family: "Exo 2"; font-size: 14px;
            font-weight: 600; color: #8b99b0;
            background: transparent;
        """)
        gl.addWidget(gt)
        gtxt = QLabel(
            "1. 在「设置」中配置 OBS 和 CS2 路径\n"
            "2. 在「Demo 库」中选择或拖入 "
            ".dem 文件\n"
            "3. 系统自动解析并检测高光时刻\n"
            "4. 在「集锦编辑」中选择要导出"
            "的片段\n"
            "5. 点击导出，自动生成高光集锦"
            "视频\n\n"
            "开启自动模式后，打完比赛即可"
            "自动生成！")
        gtxt.setWordWrap(True)
        gtxt.setStyleSheet(
            "font-size: 13px; color: #8b99b0; "
            "background: transparent; "
            "padding: 4px 0;")
        gl.addWidget(gtxt)
        gl.addStretch()
        info_layout.addWidget(gf)
        layout.addLayout(info_layout)
        layout.addStretch()

        scroll.setWidget(container)
        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.addWidget(scroll)
