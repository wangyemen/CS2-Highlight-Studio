"""
Match History Page - with clip deletion confirmation
"""
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView, QStackedWidget, QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.widgets.glow_button import GlowButton


class MatchCard(QFrame):

    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(100)
        self.setMaximumHeight(130)
        self._update_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)

        # Map
        md = record.get("map_name", "?")
        for p in ("de_", "cs_", "ar_"):
            md = md.replace(p, "")
        map_label = QLabel(md)
        map_label.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 26px; font-weight: 700; "
            "color: #e8edf5; background: transparent; min-width: 100px;")
        layout.addWidget(map_label)

        # Score
        sa = record.get("score_ct", 0)
        sb = record.get("score_t", 0)
        ta = record.get("team_a_name", "Team A")
        tb = record.get("team_b_name", "Team B")
        score_label = QLabel("{}  {} : {}  {}".format(ta, sa, sb, tb))
        score_label.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 17px; font-weight: 600; "
            "color: #00b4ff; background: transparent;")
        layout.addWidget(score_label)

        # Info
        parts = []
        date = record.get("date", "")
        if date:
            parts.append(date)
        kills = record.get("total_kills", 0)
        if kills:
            parts.append("{} kills".format(kills))
        dur = record.get("duration", 0)
        if dur > 0:
            m = int(dur) // 60
            parts.append("{}m{}s".format(m, int(dur) % 60))
        info_label = QLabel(" | ".join(parts))
        info_label.setStyleSheet(
            "font-size: 12px; color: #8b99b0; background: transparent;")
        layout.addWidget(info_label)
        layout.addStretch()

        # Highlights count
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl = record.get("highlights_count", 0)
        hl_label = QLabel(str(hl))
        hl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c = "#00b4ff" if hl > 0 else "#4a5c78"
        hl_label.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 28px; font-weight: 700; "
            "color: {}; background: transparent;".format(c))
        right.addWidget(hl_label)
        hl_text = QLabel("HL")
        hl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl_text.setStyleSheet(
            "font-size: 10px; color: #4a5c78; background: transparent;")
        right.addWidget(hl_text)
        right.addStretch()
        layout.addLayout(right)

        arrow = QLabel("\u2192")
        arrow.setStyleSheet(
            "font-size: 18px; color: #4a5c78; background: transparent;")
        layout.addWidget(arrow)

    def enterEvent(self, event):
        self.setStyleSheet(
            "MatchCard { background: #162038; border: 1px solid #00b4ff;"
            "border-radius: 10px; }")

    def leaveEvent(self, event):
        self._update_style()

    def _update_style(self):
        self.setStyleSheet(
            "MatchCard { background: #111a2e; border: 1px solid #1a2744;"
            "border-radius: 10px; }")


class MatchHistoryPage(QWidget):

    def __init__(self, settings=None, match_history=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._history = match_history
        self._current_record = None
        self._team_a_table = None
        self._team_b_table = None
        self._team_a_label = None
        self._team_b_label = None

        self.stack = QStackedWidget()
        self._build_list_page()
        self._build_detail_page()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    # ═══════════════════════════════════════
    #  List page
    # ═══════════════════════════════════════

    def _build_list_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("\u5bf9\u5c40\u8bb0\u5f55")
        title.setObjectName("heading")
        title_row.addWidget(title)
        title_row.addStretch()

        self.btn_refresh = QPushButton("\u5237\u65b0")
        self.btn_refresh.setFixedWidth(80)
        self.btn_refresh.clicked.connect(self.refresh_list)
        title_row.addWidget(self.btn_refresh)
        layout.addLayout(title_row)

        sub = QLabel("\u81ea\u52a8\u4fdd\u5b58\u7684\u5bf9\u5c40\u6570\u636e\u548c\u9ad8\u5149\u526a\u8f91\u8bb0\u5f55")
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)
        self.stack.addWidget(page)

    # ═══════════════════════════════════════
    #  Detail page
    # ═══════════════════════════════════════

    def _build_detail_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        back_row = QHBoxLayout()
        btn_back = QPushButton("\u2190 \u8fd4\u56de")
        btn_back.setFixedWidth(100)
        btn_back.clicked.connect(
            lambda: self.stack.setCurrentIndex(0))
        back_row.addWidget(btn_back)
        back_row.addStretch()
        layout.addLayout(back_row)

        # Header
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame { background: #111a2e; border: 1px solid #1a2744;
            border-radius: 12px; border-top: 2px solid #00b4ff; }
        """)
        hdr = QVBoxLayout(self.header_frame)
        hdr.setContentsMargins(24, 18, 24, 18)
        hdr.setSpacing(6)

        self.detail_map = QLabel("")
        self.detail_map.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 26px; font-weight: 700; "
            "color: #e8edf5; background: transparent;")
        hdr.addWidget(self.detail_map)

        self.detail_score = QLabel("")
        self.detail_score.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 20px; font-weight: 600; "
            "color: #00b4ff; background: transparent;")
        hdr.addWidget(self.detail_score)

        self.detail_info = QLabel("")
        self.detail_info.setStyleSheet(
            "font-size: 12px; color: #8b99b0; background: transparent;")
        hdr.addWidget(self.detail_info)

        layout.addWidget(self.header_frame)

        # Team tables
        tables_row = QHBoxLayout()
        tables_row.setSpacing(16)

        f_a, t_a, l_a = self._build_team_frame("#00b4ff")
        tables_row.addWidget(f_a)
        self._team_a_table = t_a
        self._team_a_label = l_a

        f_b, t_b, l_b = self._build_team_frame("#ff9f43")
        tables_row.addWidget(f_b)
        self._team_b_table = t_b
        self._team_b_label = l_b

        layout.addLayout(tables_row)

        # Clips
        clips_title = QLabel("\u526a\u8f91\u8bb0\u5f55")
        clips_title.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 15px; font-weight: 600; "
            "color: #8b99b0; background: transparent;")
        layout.addWidget(clips_title)

        self.clips_table = QTableWidget()
        self.clips_table.setColumnCount(6)
        self.clips_table.setHorizontalHeaderLabels(
            ["\u7c7b\u578b", "\u73a9\u5bb6", "\u65f6\u95f4",
             "\u8bc4\u5206", "\u63cf\u8ff0", "\u6587\u4ef6"])
        ch = self.clips_table.horizontalHeader()
        ch.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ch.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.clips_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clips_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.clips_table.verticalHeader().setVisible(False)
        self.clips_table.setShowGrid(False)
        self.clips_table.setAlternatingRowColors(True)
        self.clips_table.setMinimumHeight(120)
        self.clips_table.setMaximumHeight(250)
        self.clips_table.setStyleSheet("""
            QTableWidget { background: #0b1120; border: 1px solid #1a2744;
            border-radius: 8px; }
            QTableWidget::item { padding: 6px; color: #e8edf5; }
            QTableWidget::item:alternate { background: #111a2e; }
            QHeaderView::section { background: #162038; color: #8b99b0;
            border: none; border-bottom: 1px solid #1a2744;
            padding: 8px; font-size: 11px; font-weight: 600; }
        """)
        self.clips_table.cellDoubleClicked.connect(
            self._on_clip_double_click)
        layout.addWidget(self.clips_table)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_open_folder = GlowButton(
            "\u6253\u5f00\u8f93\u51fa\u76ee\u5f55", "#00e68a")
        self.btn_open_folder.setFixedWidth(160)
        self.btn_open_folder.clicked.connect(self._open_output_folder)
        btn_row.addWidget(self.btn_open_folder)

        self.btn_delete = QPushButton("\u5220\u9664\u8bb0\u5f55")
        self.btn_delete.setObjectName("dangerBtn")
        self.btn_delete.setFixedWidth(100)
        self.btn_delete.clicked.connect(self._delete_record)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        self.stack.addWidget(page)

    def _build_team_frame(self, color):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame {{ background: #111a2e; border: 1px solid #1a2744; "
            "border-radius: 10px; border-top: 2px solid {c}; }}".format(
                c=color))
        frame.setMinimumWidth(340)

        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)

        label = QLabel("Team")
        label.setStyleSheet(
            "font-family: 'Exo 2'; font-size: 13px; font-weight: 700; "
            "color: {c}; background: transparent;".format(c=color))
        v.addWidget(label)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["\u73a9\u5bb6", "K", "D", "A", "K/D", "ADR"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            hdr.setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents)
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget { background: #0b1120; border: 1px solid #1a2744;
            border-radius: 6px; font-size: 12px; }
            QTableWidget::item { padding: 5px; color: #e8edf5; }
            QTableWidget::item:alternate { background: #111a2e; }
            QHeaderView::section { background: #162038; color: #8b99b0;
            border: none; border-bottom: 1px solid #1a2744;
            padding: 6px; font-size: 11px; font-weight: 600; }
        """)
        v.addWidget(table)

        return frame, table, label

    # ═══════════════════════════════════════
    #  Fill data
    # ═══════════════════════════════════════

    def refresh_list(self):
        while self.cards_layout.count() > 0:
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        if not self._history:
            empty = QLabel(
                "\n\n\u6682\u65e0\u5bf9\u5c40\u8bb0\u5f55\n\n"
                "\u89e3\u6790 Demo \u540e\u5c06\u81ea\u52a8\u4fdd\u5b58")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                "font-size: 14px; color: #4a5c78; "
                "background: transparent; padding: 60px;")
            self.cards_layout.addWidget(empty)
            self.cards_layout.addStretch()
            return

        for record in self._history.get_recent(50):
            card = MatchCard(record)
            card.mousePressEvent = (
                lambda e, r=record: self._open_detail(r))
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _open_detail(self, record):
        self._current_record = record
        self._fill_detail(record)
        self.stack.setCurrentIndex(1)

    def _fill_detail(self, record):
        md = record.get("map_name", "?")
        for p in ("de_", "cs_", "ar_"):
            md = md.replace(p, "")
        self.detail_map.setText(md)

        sa = record.get("score_ct", 0)
        sb = record.get("score_t", 0)
        ta = record.get("team_a_name", "Team A")
        tb = record.get("team_b_name", "Team B")
        self.detail_score.setText(
            "{}  {}  :  {}  {}".format(ta, sa, sb, tb))

        self._team_a_label.setText(ta)
        self._team_b_label.setText(tb)

        parts = []
        date = record.get("date", "")
        if date:
            parts.append("\u65f6\u95f4: " + date)
        warmup = record.get("warmup_duration", 0)
        if warmup > 0:
            parts.append(
                "\u70ed\u8eab: {:.0f}\u79d2 (\u5df2\u8df3\u8fc7)".format(
                    warmup))
        dur = record.get("duration", 0)
        if dur > 0:
            mins = int(dur) // 60
            parts.append(
                "\u65f6\u957f: {}m{}s".format(mins, int(dur) % 60))
        rounds = record.get("competitive_rounds", 0)
        parts.append("{} \u56de\u5408".format(rounds))
        self.detail_info.setText(" | ".join(parts))

        self._fill_team_table(
            self._team_a_table, record.get("players_a", []))
        self._fill_team_table(
            self._team_b_table, record.get("players_b", []))
        self._fill_clips_table(record)

    def _fill_team_table(self, table, players):
        if table is None:
            return
        table.setRowCount(len(players))
        for row, p in enumerate(players):
            items = [
                p.get("name", ""),
                str(p.get("kills", 0)),
                str(p.get("deaths", 0)),
                str(p.get("assists", 0)),
                str(p.get("kd", 0)),
                str(p.get("adr", 0)),
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft
                        | Qt.AlignmentFlag.AlignVCenter)
                    item.setForeground(QColor("#e8edf5"))
                else:
                    item.setForeground(QColor("#8b99b0"))
                table.setItem(row, col, item)

    def _fill_clips_table(self, record):
        clips_info = record.get("highlights_info", [])
        clip_files = record.get("clips", [])
        self.clips_table.setRowCount(len(clips_info))

        TC = {
            "ace": "#ff3b5c", "4k": "#ff9f43", "3k": "#8b5cf6",
            "2k": "#00b4ff", "clutch": "#00e68a", "highlight": "#8b99b0",
        }

        for row, hl in enumerate(clips_info):
            ht = hl.get("type", "")
            c = TC.get(ht, "#8b99b0")
            items_data = [
                (ht.upper(), c),
                (hl.get("player", ""), "#e8edf5"),
                ("{:.1f}s".format(hl.get("start_seconds", 0)), "#8b99b0"),
                (str(int(hl.get("score", 0))), "#8b99b0"),
                (hl.get("description", ""), "#8b99b0"),
                (clip_files[row] if row < len(clip_files) else "\u2014",
                 "#4a5c78"),
            ]
            for col, (text, fg) in enumerate(items_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QColor(fg))
                if col == 4:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft
                        | Qt.AlignmentFlag.AlignVCenter)
                self.clips_table.setItem(row, col, item)

    # ═══════════════════════════════════════
    #  Actions
    # ═══════════════════════════════════════

    def _on_clip_double_click(self, row, col):
        if not self._current_record:
            return
        clips = self._current_record.get("clips", [])
        if row < len(clips) and os.path.isfile(clips[row]):
            folder = os.path.dirname(clips[row])
            if os.path.isdir(folder) and os.name == "nt":
                os.startfile(folder)

    def _open_output_folder(self):
        if not self._current_record:
            return
        d = self._current_record.get("output_dir", "")
        if d and os.path.isdir(d):
            if os.name == "nt":
                os.startfile(d)
        else:
            QMessageBox.information(
                self, "\u63d0\u793a", "\u8f93\u51fa\u76ee\u5f55\u4e0d\u5b58\u5728")

    def _delete_record(self):
        if not self._current_record:
            return

        record = self._current_record
        clip_count = len(record.get("clips", []))
        output_dir = record.get("output_dir", "")
        has_folder = output_dir and os.path.isdir(output_dir)

        # Build message
        msg = "\u786e\u5b9a\u8981\u5220\u9664\u8fd9\u6761\u5bf9\u5c40\u8bb0\u5f55\u5417\uff1f"
        if clip_count > 0:
            msg += "\n\n\u5305\u542b {} \u4e2a\u526a\u8f91\u6587\u4ef6".format(
                clip_count)
        if has_folder:
            msg += "\n\u5bf9\u5c40\u6587\u4ef6\u5939: {}".format(output_dir)

        # Ask with option to delete clips
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("\u786e\u8ba4\u5220\u9664")
        msg_box.setText(msg)

        # Custom checkbox
        cb = QCheckBox(
            "\u540c\u65f6\u5220\u9664\u6240\u6709\u526a\u8f91\u6587\u4ef6\u548c\u5bf9\u5c40\u6587\u4ef6\u5939")
        if clip_count == 0 and not has_folder:
            cb.setVisible(False)
        else:
            cb.setChecked(False)
        msg_box.setCheckBox(cb)

        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        ret = msg_box.exec()

        if ret == QMessageBox.StandardButton.Yes:
            delete_clips = cb.isChecked()
            result = self._history.delete_match(
                record["id"], delete_clips=delete_clips)

            # Handle both int and tuple return
            clips_deleted = result[0] if isinstance(result, tuple) else result

            msg2 = "\u8bb0\u5f55\u5df2\u5220\u9664"
            if delete_clips and clips_deleted and clips_deleted > 0:
                msg2 += "\n\u540c\u65f6\u5220\u9664\u4e86 {} \u4e2a\u6587\u4ef6".format(
                    clips_deleted)
            QMessageBox.information(
                self, "\u5220\u9664\u5b8c\u6210", msg2)

            self._current_record = None
            self.refresh_list()
            self.stack.setCurrentIndex(0)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_list()
