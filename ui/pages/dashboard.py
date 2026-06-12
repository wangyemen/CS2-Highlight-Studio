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
        
    @staticmethod
    def _check_ffmpeg():
        """检测 FFmpeg 是否可用"""
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

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # ── 标题 ──
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        title = QLabel("仪表盘")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()

        layout.addLayout(title_row)

        subtitle = QLabel("CS2 高光自动剪辑工作台总览")
        subtitle.setObjectName("subheading")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # ── 状态卡片行 ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.obs_card = StatusCard(
            title="OBS STUDIO",
            value="未连接",
            subtitle="通过 WebSocket 控制录制",
            accent_color="#ff3b5c",
            icon="●",
        )

        self.gsi_card = StatusCard(
            title="GSI SERVER",
            value="未启动",
            subtitle="监听 CS2 游戏状态",
            accent_color="#00b4ff",
            icon="▶",
        )

        # 改为真实检测:
        ffmpeg_ok = self._check_ffmpeg()
        if ffmpeg_ok:
            ffmpeg_value = "就绪"
            ffmpeg_color = "#00e68a"
        else:
            ffmpeg_value = "未安装"
            ffmpeg_color = "#ff3b5c"

        self.ffmpeg_card = StatusCard(
            title="FFMPEG",
            value=ffmpeg_value,
            subtitle="视频裁剪与拼接引擎",
            accent_color=ffmpeg_color,
            icon="◆",
        )

        self.highlights_card = StatusCard(
            title="高光片段",
            value="0",
            subtitle="等待解析 Demo 文件",
            accent_color="#8b5cf6",
            icon="★",
        )

        cards_layout.addWidget(self.obs_card)
        cards_layout.addWidget(self.gsi_card)
        cards_layout.addWidget(self.ffmpeg_card)
        cards_layout.addWidget(self.highlights_card)
        layout.addLayout(cards_layout)

        # ── 快速操作区域 ──
        actions_group = QFrame()
        actions_group.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(24, 20, 24, 20)
        actions_layout.setSpacing(16)

        actions_title = QLabel("快速操作")
        actions_title.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 15px;
            font-weight: 600;
            color: #e8edf5;
            background: transparent;
        """)
        actions_layout.addWidget(actions_title)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_parse = GlowButton("📂  选择 Demo 解析")
        self.btn_scan = GlowButton("🔍  扫描 Demo 文件夹", color="#8b5cf6")
        self.btn_output = GlowButton("📁  打开输出目录", color="#00e68a")

        btn_row.addWidget(self.btn_parse)
        btn_row.addWidget(self.btn_scan)
        btn_row.addWidget(self.btn_output)
        btn_row.addStretch()
        actions_layout.addLayout(btn_row)

        layout.addWidget(actions_group)

        # ── 信息区域 ──
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        # 最近活动
        recent_frame = QFrame()
        recent_frame.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(20, 16, 20, 16)
        recent_layout.setSpacing(10)

        recent_title = QLabel("最近活动")
        recent_title.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 14px;
            font-weight: 600;
            color: #8b99b0;
            background: transparent;
        """)
        recent_layout.addWidget(recent_title)

        self.recent_list = QLabel("暂无活动记录\n\n解析 Demo 或等待 GSI 检测对局结束后自动处理")
        self.recent_list.setWordWrap(True)
        self.recent_list.setStyleSheet("""
            font-size: 13px;
            color: #4a5c78;
            background: transparent;
            padding: 20px;
        """)
        recent_layout.addWidget(self.recent_list)
        recent_layout.addStretch()
        info_layout.addWidget(recent_frame)

        # 使用指南
        guide_frame = QFrame()
        guide_frame.setStyleSheet("""
            QFrame {
                background: #111a2e;
                border: 1px solid #1a2744;
                border-radius: 12px;
            }
        """)
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setContentsMargins(20, 16, 20, 16)
        guide_layout.setSpacing(10)

        guide_title = QLabel("使用指南")
        guide_title.setStyleSheet("""
            font-family: "Exo 2";
            font-size: 14px;
            font-weight: 600;
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
            "开启自动模式后，打完比赛即可自动生成！"
        )
        guide_text.setWordWrap(True)
        guide_text.setStyleSheet("""
            font-size: 13px;
            color: #8b99b0;
            background: transparent;
            line-height: 1.6;
            padding: 4px 0;
        """)
        guide_layout.addWidget(guide_text)
        guide_layout.addStretch()
        info_layout.addWidget(guide_frame)

        layout.addLayout(info_layout)
        layout.addStretch()

        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
