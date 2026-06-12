"""
集锦编辑器页面
显示高光片段，支持按玩家筛选，选择片段并一键导出
"""
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QGridLayout,
    QProgressBar, QButtonGroup,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.widgets.clip_card import ClipCard
from ui.widgets.glow_button import GlowButton


class HighlightEditorPage(QWidget):

    export_requested = pyqtSignal(list, str, str)

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._all_highlights = []
        self._clip_cards = []
        self._source_video = ""
        self._match_folder = ""
        self._players = {}          # {name: kill_count}
        self._selected_players = set()  # 空 = 全选
        self._player_buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        # ── 标题 ──
        title_row = QHBoxLayout()
        title = QLabel("集锦编辑")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()

        self.btn_select_all = QPushButton("全选")
        self.btn_select_all.setFixedWidth(70)
        self.btn_select_all.clicked.connect(self._select_all_clips)
        title_row.addWidget(self.btn_select_all)

        self.btn_deselect = QPushButton("取消全选")
        self.btn_deselect.setFixedWidth(90)
        self.btn_deselect.clicked.connect(self._deselect_all_clips)
        title_row.addWidget(self.btn_deselect)

        layout.addLayout(title_row)

        # ── 信息栏 ──
        info_bar = QHBoxLayout()
        self.info_label = QLabel(
            "尚未解析 Demo — 请先在「Demo 库」中选择并解析"
        )
        self.info_label.setObjectName("subheading")
        self.info_label.setWordWrap(True)
        info_bar.addWidget(self.info_label, 1)

        self.selected_label = QLabel("已选择: 0 片段")
        self.selected_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #00b4ff; "
            "background: transparent;"
        )
        info_bar.addWidget(self.selected_label)
        layout.addLayout(info_bar)

        # ── 视频来源 ──
        self.video_bar = QFrame()
        self.video_bar.setStyleSheet("""
            QFrame {
                background: #111a2e; border: 1px solid #1a2744;
                border-radius: 8px;
            }
        """)
        vb = QHBoxLayout(self.video_bar)
        vb.setContentsMargins(14, 8, 14, 8)
        vb.setSpacing(10)

        vb.addWidget(self._make_icon("▶", "#ff9f43"))
        vb.addWidget(self._make_label("视频来源: ", "#8b99b0"))
        self.video_name_label = QLabel("未指定")
        self.video_name_label.setStyleSheet(
            "font-size: 12px; color: #4a5c78; background: transparent;"
        )
        vb.addWidget(self.video_name_label)
        vb.addStretch()
        layout.addWidget(self.video_bar)

        # ── 玩家筛选栏 ──
        self.player_bar = QFrame()
        self.player_bar.setStyleSheet("""
            QFrame {
                background: #111a2e; border: 1px solid #1a2744;
                border-radius: 8px;
            }
        """)
        pb = QHBoxLayout(self.player_bar)
        pb.setContentsMargins(14, 8, 14, 8)
        pb.setSpacing(8)

        filter_icon = QLabel("👤")
        filter_icon.setStyleSheet(
            "font-size: 14px; background: transparent; border: none;"
        )
        pb.addWidget(filter_icon)

        filter_label = QLabel("玩家筛选:")
        filter_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #8b99b0; "
            "background: transparent; border: none;"
        )
        pb.addWidget(filter_label)

        # 玩家按钮容器
        self.player_container = QWidget()
        self.player_container.setStyleSheet("background: transparent;")
        self.player_btn_layout = QHBoxLayout(self.player_container)
        self.player_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.player_btn_layout.setSpacing(6)
        self.player_btn_layout.addStretch()
        pb.addWidget(self.player_container, 1)

        self.player_bar.hide()
        layout.addWidget(self.player_bar)

        # ── 片段网格 ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.clips_container = QWidget()
        self.clips_container.setStyleSheet("background: transparent;")
        self.clips_grid = QGridLayout(self.clips_container)
        self.clips_grid.setSpacing(12)
        self.clips_grid.setContentsMargins(0, 0, 0, 0)

        self.empty_label = QLabel(
            "\n\n  暂无高光片段\n\n"
            "  解析 Demo 后检测到的高光片段将在此显示\n"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            "font-size: 14px; color: #4a5c78; "
            "background: transparent; padding: 60px;"
        )
        self.clips_grid.addWidget(self.empty_label, 0, 0, 1, 3)

        self.scroll_area.setWidget(self.clips_container)
        layout.addWidget(self.scroll_area, 1)

        # ── 底部操作栏 ──
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("""
            QFrame {
                background: #0b1120;
                border-top: 1px solid #1a2744;
            }
        """)
        bl = QHBoxLayout(bottom_bar)
        bl.setContentsMargins(24, 12, 24, 12)

        left_info = QVBoxLayout()
        left_info.setSpacing(4)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        left_info.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(
            "font-size: 12px; color: #8b99b0; background: transparent;"
        )
        self.progress_label.hide()
        left_info.addWidget(self.progress_label)
        left_info.addStretch()
        bl.addLayout(left_info, 1)

        self.btn_export = GlowButton("✂  导出选中集锦", "#00e68a")
        self.btn_export.setFixedWidth(200)
        self.btn_export.setFixedHeight(44)
        self.btn_export.clicked.connect(self._on_export)
        bl.addWidget(self.btn_export)

        layout.addWidget(bottom_bar)

    # ═══════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════

    @staticmethod
    def _make_icon(text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 14px; color: {c}; background: transparent; "
            "border: none;".format(c=color)
        )
        return lbl

    @staticmethod
    def _make_label(text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 12px; color: {c}; background: transparent; "
            "border: none;".format(c=color)
        )
        return lbl

    @staticmethod
    def _make_player_button(name, count):
        text = "{} ({})".format(name, count)
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(True)
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 180, 255, 0.15);
                border: 1px solid #00b4ff;
                border-radius: 14px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
                color: #00b4ff;
            }
            QPushButton:hover {
                background: rgba(0, 180, 255, 0.25);
            }
            QPushButton:unchecked {
                background: #162038;
                border: 1px solid #1a2744;
                color: #4a5c78;
            }
        """)
        return btn

    # ═══════════════════════════════════════
    #  数据设置
    # ═══════════════════════════════════════

    def set_highlights(self, highlights, video_path=""):
        self._all_highlights = highlights
        self._source_video = video_path
        self._extract_players()
        self._refresh_player_bar()
        self._apply_filter()
        self._update_video_bar()
        
    def set_match_folder(self, folder):
        self._match_folder = folder    
    
    def _extract_players(self):
        """从高光片段中提取玩家列表"""
        players = {}
        for hl in self._all_highlights:
            name = hl.player
            if name not in players:
                players[name] = 0
            players[name] += hl.kill_count
        self._players = players
        self._selected_players.clear()

    def _refresh_player_bar(self):
        """重建玩家筛选按钮"""
        # 清空
        while self.player_btn_layout.count() > 0:
            item = self.player_btn_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self._player_buttons.clear()

        if not self._players:
            self.player_bar.hide()
            return

        self.player_bar.show()

        # "全部" 按钮
        btn_all = QPushButton("全部 ({})".format(len(self._players)))
        btn_all.setCheckable(True)
        btn_all.setChecked(True)
        btn_all.setFixedHeight(30)
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.setStyleSheet("""
            QPushButton {
                background: rgba(0, 230, 138, 0.15);
                border: 1px solid #00e68a;
                border-radius: 14px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 700;
                color: #00e68a;
            }
            QPushButton:hover {
                background: rgba(0, 230, 138, 0.25);
            }
            QPushButton:unchecked {
                background: #162038;
                border: 1px solid #1a2744;
                color: #4a5c78;
            }
        """)
        btn_all.clicked.connect(self._on_all_player_clicked)
        self.player_btn_layout.addWidget(btn_all)
        self._btn_all = btn_all

        # 各玩家按钮
        sorted_players = sorted(
            self._players.items(), key=lambda x: x[1], reverse=True
        )
        for name, count in sorted_players:
            btn = self._make_player_button(name, count)
            btn.clicked.connect(
                lambda checked, n=name: self._on_player_clicked(n, checked)
            )
            self.player_btn_layout.addWidget(btn)
            self._player_buttons[name] = btn

        self.player_btn_layout.addStretch()

    def _on_all_player_clicked(self):
        """点击「全部」按钮"""
        self._selected_players.clear()
        # 全部设为选中
        for btn in self._player_buttons.values():
            btn.setChecked(True)
        self._btn_all.setChecked(True)
        self._apply_filter()

    def _on_player_clicked(self, name, checked):
        """点击单个玩家按钮"""
        if checked:
            self._selected_players.add(name)
        else:
            self._selected_players.discard(name)

        # 更新「全部」按钮状态
        all_checked = len(self._selected_players) == len(self._players)
        self._btn_all.setChecked(all_checked)

        self._apply_filter()

    def _apply_filter(self):
        """根据选中玩家筛选高光片段"""
        if not self._selected_players:
            filtered = self._all_highlights
        else:
            filtered = [
                h for h in self._all_highlights
                if h.player in self._selected_players
            ]
        self._refresh_grid(filtered)
        self._update_info(filtered)

    def _update_video_bar(self):
        if self._source_video:
            name = Path(self._source_video).name
            size_mb = (
                os.path.getsize(self._source_video) / (1024 * 1024)
                if os.path.exists(self._source_video) else 0
            )
            self.video_name_label.setText(
                "{} ({:.1f} MB)".format(name, size_mb)
            )
            self.video_name_label.setStyleSheet(
                "font-size: 12px; color: #00e68a; "
                "background: transparent; font-weight: 600;"
            )
        else:
            self.video_name_label.setText(
                "未指定 — 请在 Demo 库中关联视频"
            )
            self.video_name_label.setStyleSheet(
                "font-size: 12px; color: #ff3b5c; "
                "background: transparent;"
            )

    def _refresh_grid(self, highlights):
        for card in self._clip_cards:
            card.setParent(None)
            card.deleteLater()
        self._clip_cards.clear()

        if self.empty_label:
            self.empty_label.setParent(None)
            self.empty_label.deleteLater()
            self.empty_label = None

        if not highlights:
            self.empty_label = QLabel(
                "\n\n  暂无匹配的高光片段\n\n"
                "  尝试选择其他玩家或取消筛选\n"
            )
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty_label.setStyleSheet(
                "font-size: 14px; color: #4a5c78; "
                "background: transparent; padding: 60px;"
            )
            self.clips_grid.addWidget(self.empty_label, 0, 0, 1, 3)
            return

        cols = 2
        for i, hl in enumerate(highlights):
            card = ClipCard(hl)
            card.toggled.connect(self._on_card_toggled)
            self._clip_cards.append(card)
            row = i // cols
            col = i % cols
            self.clips_grid.addWidget(card, row, col)

    def _update_info(self, filtered=None):
        total = len(self._all_highlights)
        if filtered is not None:
            shown = len(filtered)
        else:
            shown = total
        selected = sum(1 for c in self._clip_cards if c.is_checked)

        if shown == total:
            self.info_label.setText(
                "共检测到 {} 个高光片段".format(total)
            )
        else:
            self.info_label.setText(
                "共 {} 个片段, 当前显示 {} 个".format(total, shown)
            )
        self.selected_label.setText("已选择: {} 片段".format(selected))

    def _on_card_toggled(self, hl_id, checked):
        self._update_info()

    # ═══════════════════════════════════════
    #  操作
    # ═══════════════════════════════════════

    def _select_all_clips(self):
        for card in self._clip_cards:
            card.checkbox.setChecked(True)
        self._update_info()

    def _deselect_all_clips(self):
        for card in self._clip_cards:
            card.checkbox.setChecked(False)
        self._update_info()

    def get_selected_highlights(self):
        return [
            card.highlight
            for card in self._clip_cards
            if card.is_checked
        ]

    def _on_export(self):
        selected = self.get_selected_highlights()
        if not selected:
            return

        if not self._source_video:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "缺少视频文件",
                "请先在「Demo 库」页面选择对应的 OBS 录制视频。\n\n"
                "Demo 文件仅包含游戏数据，\n"
                "裁剪高光片段需要对应的视频文件。",
            )
            return

        output_dir = ""
        if self.settings:
            output_dir = self.settings.get("output_dir", "")

        if not output_dir:
            from PyQt6.QtWidgets import QFileDialog
            output_dir = QFileDialog.getExistingDirectory(
                self, "选择输出目录"
            )
            if not output_dir:
                return
            if self.settings:
                self.settings.set("output_dir", output_dir)
                self.settings.save()

        self.export_requested.emit(
            selected, self._source_video, output_dir
        )

    def show_progress(self, current, total, message):
        self.progress_bar.show()
        self.progress_label.show()
        self.progress_bar.setMaximum(max(total, 1))
        self.progress_bar.setValue(current)
        self.progress_label.setText(message)

    def hide_progress(self):
        self.progress_bar.hide()
        self.progress_label.hide()
