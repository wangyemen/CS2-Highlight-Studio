"""
仪表盘页面 - 总览和快速操作
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt

from ui.widgets.status_card import StatusCard
from ui.widgets.glow_button import GlowButton


class DashboardPage(QWidget):

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()
        self._connect_clicks()

    @staticmethod
    def _check_ffmpeg():
        import subprocess
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _connect_clicks(self):
        """Make cards clickable to refresh."""
        self.obs_card.installEventFilter(self)
        self.gsi_card.installEventFilter(self)
        self.ffmpeg_card.installEventFilter(self)

        self.obs_card.setCursor(
            Qt.CursorShape.PointingHandCursor)
        self.gsi_card.setCursor(
            Qt.CursorShape.PointingHandCursor)
        self.ffmpeg_card.setCursor(
            Qt.CursorShape.PointingHandCursor)

    def eventFilter(self, obj, event):
        if (event.type()
                == event.Type.MouseButtonRelease):
            if obj is self.obs_card:
                self._refresh_obs()
                return True
            elif obj is self.gsi_card:
                self._refresh_gsi()
                return True
            elif obj is self.ffmpeg_card:
                self._refresh_ffmpeg()
                return True
        return super().eventFilter(obj, event)

    def _refresh_obs(self):
        """Refresh OBS status card."""
        self.obs_card.set_value(
            "检测中...", "#ff9f43")
        # Actual status updated by main_window timer
        # Force update now
        try:
            from ui.main_window import MainWindow
            parent = self.window()
            if parent and hasattr(parent, 'obs'):
                if parent.obs.state.connected:
                    if parent.obs.state.recording:
                        self.obs_card.set_value(
                            "录制中", "#ff3b5c")
                    else:
                        self.obs_card.set_value(
                            "已连接(空闲)", "#00e68a")
                else:
                    self.obs_card.set_value(
                        "未连接", "#ff3b5c")
        except Exception:
            self.obs_card.set_value(
                "未连接", "#ff3b5c")

    def _refresh_gsi(self):
        """Refresh GSI status card."""
        self.gsi_card.set_value(
            "检测中...", "#ff9f43")
        try:
            parent = self.window()
            if parent and hasattr(parent, 'gsi'):
                gsi = parent.gsi
                if gsi.is_gsi_receiving():
                    self.gsi_card.set_value(
                        "接收中", "#00e68a")
                elif gsi.state.connected:
                    self.gsi_card.set_value(
                        "等待数据", "#ff9f43")
                else:
                    self.gsi_card.set_value(
                        "未启动", "#ff3b5c")
        except Exception:
            self.gsi_card.set_value(
                "未启动", "#ff3b5c")

    def _refresh_ffmpeg(self):
        """Refresh FFmpeg status card."""
        self.ffmpeg_card.set_value(
            "检测中...", "#ff9f43")
        ok = self._check_ffmpeg()
        if ok:
            self.ffmpeg_card.set_value(
                "就绪", "#00e68a")
        else:
            # Check settings path
            try:
                parent = self.window()
                if parent and hasattr(
                        parent, 'settings'):
                    path = parent.settings.get(
                        "ffmpeg_path", "")
                    if path:
                        import os
                        if os.path.isfile(path):
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
        scroll.setFrameShape(QFrame.Shape.NoFrame)
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

        # Status cards
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

        ffmpeg_ok = self._check_ffmpeg()
        ffmpeg_value = "就绪" if ffmpeg_ok else "未安装"
        ffmpeg_color = (
            "#00e68a" if ffmpeg_ok else "#ff3b5c")

        self.ffmpeg_card = StatusCard(
            title="FFMPEG",
            value=ffmpeg_value,
            subtitle="视频裁剪与拼接引擎",
            accent_color=ffmpeg_color,
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
        cards_layout.addWidget(self.highlights_card)
        layout.addLayout(cards_layout)

        # Hint
        hint = QLabel(
            "\u2139 点击状态卡片可刷新检测")
        hint.setStyleSheet(
            "font-size: 11px; color: #4a5c78; "
            "background: transparent;")
        layout.addWidget(hint)

        # Quick actions
        actions_group = QFrame()
        actions_group.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(
            24, 20, 24, 20)
        actions_layout.setSpacing(16)

        actions_title = QLabel("快速操作")
        actions_title.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 15px; font-weight: 600;
            color: #e8edf5;
            background: transparent;
        """)
        actions_layout.addWidget(actions_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_parse = GlowButton(
            "\U0001f4c2  选择 Demo 解析")
        self.btn_scan = GlowButton(
            "\U0001f50d  扫描 Demo 文件夹",
            color="#8b5cf6")
        self.btn_output = GlowButton(
            "\U0001f4c1  打开输出目录",
            color="#00e68a")

        btn_row.addWidget(self.btn_parse)
        btn_row.addWidget(self.btn_scan)
        btn_row.addWidget(self.btn_output)
        btn_row.addStretch()
        actions_layout.addLayout(btn_row)
        layout.addWidget(actions_group)

        # Info area
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        recent_frame = QFrame()
        recent_frame.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(
            20, 16, 20, 16)
        recent_layout.setSpacing(10)
        recent_title = QLabel("最近活动")
        recent_title.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 14px; font-weight: 600;
            color: #8b99b0;
            background: transparent;
        """)
        recent_layout.addWidget(recent_title)
        self.recent_list = QLabel(
            "暂无活动记录\n\n解析 Demo 或等待 "
            "GSI 检测对局结束后自动处理")
        self.recent_list.setWordWrap(True)
        self.recent_list.setStyleSheet(
            "font-size: 13px; color: #4a5c78; "
            "background: transparent; padding: 20px;")
        recent_layout.addWidget(self.recent_list)
        recent_layout.addStretch()
        info_layout.addWidget(recent_frame)

        guide_frame = QFrame()
        guide_frame.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setContentsMargins(
            20, 16, 20, 16)
        guide_layout.setSpacing(10)
        guide_title = QLabel("使用指南")
        guide_title.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 14px; font-weight: 600;
            color: #8b99b0;
            background: transparent;
        """)
        guide_layout.addWidget(guide_title)
        guide_text = QLabel(
            "1. 在「设置」中配置 OBS 和 CS2 路径\n"
            "2. 在「Demo 库」中选择或拖入 .dem 文件\n"
            "3. 系统自动解析并检测高光时刻\n"
            "4. 在「集锦编辑」中选择要导出的片段\n"
            "5. 点击导出，自动生成高光集锦视频\n\n"
            "开启自动模式后，打完比赛即可自动生成！")
        guide_text.setWordWrap(True)
        guide_text.setStyleSheet(
            "font-size: 13px; color: #8b99b0; "
            "background: transparent; padding: 4px 0;")
        guide_layout.addWidget(guide_text)
        guide_layout.addStretch()
        info_layout.addWidget(guide_frame)
        layout.addLayout(info_layout)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
