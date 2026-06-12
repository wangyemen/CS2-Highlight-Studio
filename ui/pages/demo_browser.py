"""
Demo 文件管理页面
支持拖放、扫描、选择 Demo 文件 + 关联视频文件
"""
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from ui.widgets.glow_button import GlowButton


class DemoScanWorker(QThread):
    """后台扫描 Demo 文件"""
    found = pyqtSignal(list)

    def __init__(self, folders: list):
        super().__init__()
        self.folders = folders

    def run(self):
        demos = []
        for folder in self.folders:
            p = Path(folder)
            if p.exists():
                for f in p.rglob("*.dem"):
                    demos.append(str(f))
        self.found.emit(demos)


class DemoBrowserPage(QWidget):

    demo_selected = pyqtSignal(str)
    parse_requested = pyqtSignal(str, str)   # demo_path, video_path

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._demos = []
        self._video_path = ""
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── 标题行 ──
        title_row = QHBoxLayout()
        title = QLabel("Demo 库")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()

        self.btn_scan = GlowButton("扫描文件夹", "#8b5cf6")
        self.btn_scan.setFixedWidth(130)
        self.btn_scan.clicked.connect(self._scan_folders)
        title_row.addWidget(self.btn_scan)

        self.btn_add_folder = QPushButton("添加目录")
        self.btn_add_folder.setFixedWidth(90)
        self.btn_add_folder.clicked.connect(self._add_folder)
        title_row.addWidget(self.btn_add_folder)

        layout.addLayout(title_row)

        subtitle = QLabel("拖放 .dem 文件到此处，或点击扫描已有 Demo 文件")
        subtitle.setObjectName("subheading")
        layout.addWidget(subtitle)

        # ── 拖放区域 ──
        self.drop_zone = QFrame()
        self.drop_zone.setObjectName("dropZone")
        self.drop_zone.setFixedHeight(100)
        self.drop_zone.setStyleSheet("""
            QFrame#dropZone {
                border: 2px dashed #1a2744;
                border-radius: 12px;
                background: #111a2e;
            }
        """)

        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        drop_text = QLabel("拖放 .dem 文件到此处")
        drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_text.setStyleSheet(
            "font-size: 14px; color: #4a5c78; background: transparent; "
            "border: none;"
        )
        drop_layout.addWidget(drop_text)

        layout.addWidget(self.drop_zone)

        # ── 主内容: Demo列表 + 视频关联 ──
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # 左侧: Demo 列表
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        demo_label = QLabel("Demo 文件")
        demo_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #8b99b0; "
            "background: transparent; text-transform: uppercase; "
            "letter-spacing: 1px;"
        )
        left_panel.addWidget(demo_label)

        self.demo_list = QListWidget()
        self.demo_list.setMinimumHeight(260)
        self.demo_list.currentItemChanged.connect(self._on_selection_changed)
        left_panel.addWidget(self.demo_list)

        content_row.addLayout(left_panel, 2)

        # 右侧: 视频文件关联
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        video_label = QLabel("关联 OBS 录制视频")
        video_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #8b99b0; "
            "background: transparent; text-transform: uppercase; "
            "letter-spacing: 1px;"
        )
        right_panel.addWidget(video_label)

        video_desc = QLabel(
            "选择该对局对应的 OBS 录制视频文件 (.mp4 / .mkv / .flv)\n"
            "剪辑引擎将从视频中裁剪出高光片段"
        )
        video_desc.setWordWrap(True)
        video_desc.setStyleSheet(
            "font-size: 12px; color: #4a5c78; background: transparent; "
            "padding: 4px 0;"
        )
        right_panel.addWidget(video_desc)

        # 视频路径显示
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("""
            QFrame {
                background: #0b1120;
                border: 1px solid #1a2744;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        video_frame_layout = QVBoxLayout(self.video_frame)
        video_frame_layout.setContentsMargins(12, 10, 12, 10)
        video_frame_layout.setSpacing(8)

        self.video_path_label = QLabel("未选择视频文件")
        self.video_path_label.setWordWrap(True)
        self.video_path_label.setStyleSheet(
            "font-size: 12px; color: #4a5c78; background: transparent;"
        )
        video_frame_layout.addWidget(self.video_path_label)

        # 视频信息
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent;"
        )
        video_frame_layout.addWidget(self.video_info_label)

        right_panel.addWidget(self.video_frame)

        # 选择视频按钮
        video_btn_row = QHBoxLayout()
        video_btn_row.setSpacing(8)

        self.btn_select_video = QPushButton("选择视频文件")
        self.btn_select_video.clicked.connect(self._select_video)
        video_btn_row.addWidget(self.btn_select_video)

        self.btn_clear_video = QPushButton("清除")
        self.btn_clear_video.setFixedWidth(60)
        self.btn_clear_video.clicked.connect(self._clear_video)
        video_btn_row.addWidget(self.btn_clear_video)

        video_btn_row.addStretch()
        right_panel.addLayout(video_btn_row)

        # 自动匹配提示
        self.auto_match_label = QLabel(
            "提示: 选择 Demo 后可点击「自动匹配」\n"
            "系统会根据文件时间戳在 OBS 录制目录中搜索对应视频"
        )
        self.auto_match_label.setWordWrap(True)
        self.auto_match_label.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent; "
            "padding: 8px 0;"
        )
        right_panel.addWidget(self.auto_match_label)

        self.btn_auto_match = GlowButton("自动匹配视频", "#ff9f43")
        self.btn_auto_match.setFixedWidth(160)
        self.btn_auto_match.clicked.connect(self._auto_match_video)
        right_panel.addWidget(self.btn_auto_match)

        right_panel.addStretch()
        content_row.addLayout(right_panel, 1)

        layout.addLayout(content_row, 1)

        # ── 底部操作栏 ──
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        self.btn_parse = GlowButton("▶  解析 Demo 并检测高光")
        self.btn_parse.setFixedWidth(240)
        self.btn_parse.clicked.connect(self._on_parse)
        bottom_row.addWidget(self.btn_parse)

        self.btn_parse_all = QPushButton("解析全部")
        self.btn_parse_all.setFixedWidth(100)
        bottom_row.addWidget(self.btn_parse_all)

        bottom_row.addStretch()

        self.status_label = QLabel("共 0 个 Demo 文件")
        self.status_label.setObjectName("muted")
        bottom_row.addWidget(self.status_label)

        layout.addLayout(bottom_row)

    # ═══════════════════════════════════════
    #  拖放
    # ═══════════════════════════════════════

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_zone.setStyleSheet("""
                QFrame#dropZone {
                    border: 2px dashed #00b4ff;
                    border-radius: 12px;
                    background: rgba(0, 180, 255, 0.08);
                }
            """)

    def dragLeaveEvent(self, event):
        self.drop_zone.setStyleSheet("""
            QFrame#dropZone {
                border: 2px dashed #1a2744;
                border-radius: 12px;
                background: #111a2e;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.drop_zone.setStyleSheet("""
            QFrame#dropZone {
                border: 2px dashed #1a2744;
                border-radius: 12px;
                background: #111a2e;
            }
        """)

        for url in event.mimeData().urls():
            path = url.toLocalFile()
            lower = path.lower()
            if lower.endswith(".dem"):
                self._add_demo(path)
            elif lower.endswith((".mp4", ".mkv", ".flv", ".ts", ".avi")):
                self._set_video(path)

    # ═══════════════════════════════════════
    #  Demo 管理
    # ═══════════════════════════════════════

    def _add_demo(self, filepath):
        if filepath in self._demos:
            return
        self._demos.append(filepath)
        name = Path(filepath).name
        item = QListWidgetItem("  " + name)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        item.setToolTip(filepath)
        self.demo_list.addItem(item)
        self._update_status()

    def _scan_folders(self):
        if not self.settings:
            return

        folders = []
        cs2_path = self.settings.get("cs2_install_path", "")
        if cs2_path:
            # 尝试多个可能的 replay 目录
            for sub in ("game/csgo/replays", "csgo/replays", "replays"):
                replay_dir = Path(cs2_path) / sub
                if replay_dir.exists():
                    folders.append(str(replay_dir))
                    break

        for f in self.settings.get("demo_scan_folders", []):
            if os.path.exists(f):
                folders.append(f)

        if not folders:
            folders.append(str(Path.home() / "Downloads"))

        self.worker = DemoScanWorker(folders)
        self.worker.found.connect(self._on_demos_found)
        self.worker.start()

    def _on_demos_found(self, demos):
        for demo in demos:
            self._add_demo(demo)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择 Demo 文件夹")
        if folder:
            for f in Path(folder).rglob("*.dem"):
                self._add_demo(str(f))

    def _on_selection_changed(self, current, previous):
        if current:
            filepath = current.data(Qt.ItemDataRole.UserRole)
            self.demo_selected.emit(filepath)

    # ═══════════════════════════════════════
    #  视频文件管理
    # ═══════════════════════════════════════

    def _select_video(self):
        video_exts = "视频文件 (*.mp4 *.mkv *.flv *.ts *.avi);;所有文件 (*)"
        start_dir = ""
        if self.settings:
            start_dir = self.settings.get("output_dir", "")

        path, _ = QFileDialog.getOpenFileName(
            self, "选择 OBS 录制的视频文件", start_dir, video_exts
        )
        if path:
            self._set_video(path)

    def _set_video(self, path):
        self._video_path = path
        name = Path(path).name
        size_mb = os.path.getsize(path) / (1024 * 1024) if os.path.exists(path) else 0
        self.video_path_label.setText(name)
        self.video_path_label.setStyleSheet(
            "font-size: 12px; color: #00e68a; background: transparent; "
            "font-weight: 600;"
        )
        self.video_info_label.setText(
            "{} | {:.1f} MB".format(path, size_mb)
        )
        self.video_info_label.setStyleSheet(
            "font-size: 11px; color: #4a5c78; background: transparent;"
        )

    def _clear_video(self):
        self._video_path = ""
        self.video_path_label.setText("未选择视频文件")
        self.video_path_label.setStyleSheet(
            "font-size: 12px; color: #4a5c78; background: transparent;"
        )
        self.video_info_label.setText("")

    def _auto_match_video(self):
        """根据 Demo 文件时间自动搜索对应视频"""
        current = self.demo_list.currentItem()
        if not current:
            self.auto_match_label.setText("请先选择一个 Demo 文件")
            return

        demo_path = current.data(Qt.ItemDataRole.UserRole)
        demo_mtime = os.path.getmtime(demo_path)

        # 搜索范围: OBS 默认录制目录
        search_dirs = []
        if self.settings:
            # 用户可能配置了 OBS 录制路径
            output = self.settings.get("output_dir", "")
            if output:
                search_dirs.append(output)

        # 常见 OBS 录制路径
        home = Path.home()
        for sub in ("Videos", "Videos/OBS", "Documents/OBS"):
            candidate = home / sub
            if candidate.exists():
                search_dirs.append(str(candidate))

        # 各盘符
        for letter in "CDEFGH":
            for sub in ("Videos", "OBS", "OBS录制", "录像"):
                candidate = Path("{}:/{}".format(letter, sub))
                if candidate.exists():
                    search_dirs.append(str(candidate))

        video_exts = {".mp4", ".mkv", ".flv", ".ts"}
        best_match = None
        best_diff = float("inf")

        for search_dir in search_dirs:
            p = Path(search_dir)
            if not p.exists():
                continue
            for vf in p.rglob("*"):
                if vf.suffix.lower() in video_exts:
                    v_mtime = vf.stat().st_mtime
                    diff = abs(v_mtime - demo_mtime)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = str(vf)

        if best_match and best_diff < 3600:
            # 1 小时内的时间差视为匹配
            self._set_video(best_match)
            self.auto_match_label.setText(
                "自动匹配成功 (时间差: {:.0f} 秒)".format(best_diff)
            )
            self.auto_match_label.setStyleSheet(
                "font-size: 11px; color: #00e68a; background: transparent; "
                "padding: 8px 0;"
            )
        else:
            self.auto_match_label.setText(
                "未找到匹配视频，请手动选择"
            )
            self.auto_match_label.setStyleSheet(
                "font-size: 11px; color: #ff9f43; background: transparent; "
                "padding: 8px 0;"
            )

    # ═══════════════════════════════════════
    #  解析触发
    # ═══════════════════════════════════════

    def _on_parse(self):
        current = self.demo_list.currentItem()
        if not current:
            return

        demo_path = current.data(Qt.ItemDataRole.UserRole)
        self.parse_requested.emit(demo_path, self._video_path)

    def _update_status(self):
        count = len(self._demos)
        self.status_label.setText("共 {} 个 Demo 文件".format(count))

    def get_selected_demo(self):
        current = self.demo_list.currentItem()
        if current:
            return current.data(Qt.ItemDataRole.UserRole)
        return ""

    def get_video_path(self):
        return self._video_path
