"""
Video Clipper Page - threaded export with real-time progress
"""
import os
import subprocess

_CREATION_FLAGS = 0
if os.name == "nt":
    _CREATION_FLAGS = 0x08000000  # CREATE_NO_WINDOW

import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog,
    QMessageBox, QSizePolicy, QProgressBar,
)
from PyQt6.QtCore import (
    Qt, QThread, QUrl, pyqtSignal,
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QShortcut, QKeySequence

from ui.widgets.glow_button import GlowButton
from ui.widgets.timeline import TimelineWidget


def _fmt(sec):
    sec = max(0, sec)
    m = int(sec) // 60
    s = sec - m * 60
    return "{:02d}:{:05.2f}".format(m, s)


def _fmt_dur(sec):
    """Format remaining time as human-readable."""
    sec = max(0, int(sec))
    if sec < 60:
        return "{}\u79d2".format(sec)
    m = sec // 60
    s = sec % 60
    if m < 60:
        return "{}\u5206{}\u79d2".format(m, s)
    h = m // 60
    m = m % 60
    return "{}\u5c0f\u65f6{}\u5206".format(h, m)


def _find_ffmpeg():
    for name in ("ffmpeg", "ffmpeg.exe"):
        try:
            r = subprocess.run(
                [name, "-version"],
                capture_output=True, timeout=5,
                creationflags=_CREATION_FLAGS)
            if r.returncode == 0:
                return name
        except Exception:
            pass
    for p in (
        r"C:\ffmpeg\bin\ffmpeg.exe",
        os.path.expandvars(
            r"%LOCALAPPDATA%\ffmpeg\bin\ffmpeg.exe"),
    ):
        if os.path.isfile(p):
            return p
    return "ffmpeg"


def _find_ffprobe():
    for name in ("ffprobe", "ffprobe.exe"):
        try:
            r = subprocess.run(
                [name, "-version"],
                capture_output=True, timeout=5,
                creationflags=_CREATION_FLAGS)
            if r.returncode == 0:
                return name
        except Exception:
            pass
    for p in (
        r"C:\ffmpeg\bin\ffprobe.exe",
        os.path.expandvars(
            r"%LOCALAPPDATA%\ffmpeg\bin\ffprobe.exe"),
    ):
        if os.path.isfile(p):
            return p
    return "ffprobe"


# ═══════════════════════════════════════
#  Duration loader
# ═══════════════════════════════════════

class _DurationLoader(QThread):
    done = pyqtSignal(str, float)

    def __init__(self, path):
        super().__init__()
        self._p = path

    def run(self):
        d = 0.0
        try:
            r = subprocess.run(
                [_find_ffprobe(), "-v", "error",
                 "-show_entries", "format=duration",
                 "-of",
                 "default=noprint_wrappers=1:nokey=1",
                 self._p],
                capture_output=True, timeout=15,
                encoding="utf-8", errors="replace",
                creationflags=_CREATION_FLAGS)
            if r.returncode == 0 and r.stdout.strip():
                d = float(
                    r.stdout.strip().split("\n")[0])
        except Exception:
            pass
        self.done.emit(self._p, d)


# ═══════════════════════════════════════
#  Export worker with real-time FFmpeg progress
# ═══════════════════════════════════════

class _ExportWorker(QThread):
    # (percent 0-100, message, detail)
    progress = pyqtSignal(int, str, str)
    finished = pyqtSignal(list)

    def __init__(self, source, segments, output_dir,
                 base_name, ffmpeg):
        super().__init__()
        self._source = source
        self._segments = segments
        self._output_dir = output_dir
        self._base = base_name
        self._ffmpeg = ffmpeg
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        clips = []
        total = len(self._segments)
        t_start = time.time()
        total_dur = sum(e - s for s, e in
                        self._segments)

        for i, (s, e) in enumerate(self._segments):
            if self._cancel:
                break

            out = os.path.join(
                self._output_dir,
                "{}_part{:02d}.mp4".format(
                    self._base, i + 1))

            seg_dur = e - s
            base_pct = int(i / total * 100)
            seg_weight = 100.0 / total

            self.progress.emit(
                base_pct,
                "\u5bfc\u51fa {}/{} \u2192 "
                "{:.1f}s ~ {:.1f}s".format(
                    i + 1, total, s, e),
                "")

            ok = self._fast_clip(
                s, e, out, seg_dur,
                base_pct, seg_weight,
                t_start, total_dur)

            if ok:
                clips.append(out)

        self.finished.emit(clips)

    def _fast_clip(self, start, end, out, seg_dur,
                   base_pct, seg_weight,
                   t_start, total_dur):
        """Stream copy with real-time progress."""
        cmd = [
            self._ffmpeg, "-y",
            "-loglevel", "error",
            "-fflags", "+discardcorrupt",
            "-noaccurate_seek",
            "-ss", "{:.3f}".format(start),
            "-i", self._source,
            "-t", "{:.3f}".format(seg_dur),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            out,
        ]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                creationflags=_CREATION_FLAGS)
        except Exception as ex:
            print("FFmpeg launch failed:", ex)
            return False

        # Parse real-time progress
        while True:
            if self._cancel:
                try:
                    proc.kill()
                except Exception:
                    pass
                return False

            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break

            if line.startswith("out_time_us="):
                try:
                    us_str = line.strip().split("=")[1]
                    us = int(us_str)
                    if us < 0:
                        us = 0
                    seg_pct = min(1.0,
                        us / (seg_dur * 1000000))
                    pct = int(
                        base_pct + seg_pct * seg_weight)

                    # Time estimate
                    elapsed = time.time() - t_start
                    if seg_pct > 0.01:
                        total_est = elapsed / (
                            pct / 100.0) if pct > 0 \
                            else 0
                        remaining = max(
                            0, total_est - elapsed)
                        eta = "\u5269\u4f59 " + \
                            _fmt_dur(remaining)
                    else:
                        eta = ""

                    detail = "\u6d41\u590d\u5236 " + \
                        "{:.0f}%".format(
                            seg_pct * 100)
                    self.progress.emit(
                        pct,
                        "\u5bfc\u51fa \u2192 "
                        "{:.1f}s ~ {:.1f}s".format(
                            start, end),
                        "{}  {}".format(
                            detail, eta))
                except (ValueError, IndexError):
                    pass

        proc.wait()

        if proc.returncode != 0:
            stderr = proc.stderr.read() if \
                proc.stderr else ""
            if stderr:
                print("FFmpeg error:", stderr[:200])

        return (proc.returncode == 0
                and os.path.isfile(out))


# ═══════════════════════════════════════
#  Drop zone
# ═══════════════════════════════════════

class _DropZone(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(70)
        self._n = (
            "QFrame { background: #0b1120; "
            "border: 2px dashed #2a3a5c;"
            "border-radius: 12px; }")
        self._h = (
            "QFrame { background: #111a2e; "
            "border: 2px dashed #00b4ff;"
            "border-radius: 12px; }")
        self.setStyleSheet(self._n)
        lay = QVBoxLayout(self)
        lay.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        t = QLabel(
            "\U0001f4c1  \u62d6\u653e\u89c6\u9891"
            "\u5230\u6b64\u5904\uff0c\u6216\u70b9"
            "\u51fb\u4e0b\u65b9\u6d4f\u89c8")
        t.setStyleSheet(
            "font-size: 13px; color: #8b99b0; "
            "background: transparent;")
        t.setAlignment(
            Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                p = u.toLocalFile().lower()
                if p.endswith((".mp4", ".mkv",
                    ".flv", ".mov", ".ts")):
                    event.acceptProposedAction()
                    self.setStyleSheet(self._h)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._n)

    def dropEvent(self, event):
        self.setStyleSheet(self._n)
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if p.lower().endswith(
                (".mp4", ".mkv", ".flv",
                 ".mov", ".ts")):
                self.file_dropped.emit(p)
                return


# ═══════════════════════════════════════
#  Main page
# ═══════════════════════════════════════

class VideoClipperPage(QWidget):

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._video_path = ""
        self._duration = 0.0
        self._ffmpeg = None
        self._loader = None
        self._exporter = None
        self._fullscreen = False

        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus)
        self.installEventFilter(self)
        self._build()
        self._bind()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(8)

        # Top
        top = QHBoxLayout()
        title = QLabel("\u89c6\u9891\u526a\u8f91")
        title.setObjectName("heading")
        top.addWidget(title)
        top.addStretch()
        sub = QLabel(
            "Space=\u64ad\u653e  S=\u526a\u5207  "
            "Del=\u5220\u9664  Ctrl+E=\u5bfc\u51fa"
            "  \u00b1=\u7f29\u653e")
        sub.setStyleSheet(
            "font-size: 11px; color: #4a5c78; "
            "background: transparent;")
        top.addWidget(sub)
        root.addLayout(top)

        # Drop
        self._drop = _DropZone()
        self._drop.file_dropped.connect(
            self._load_video)
        root.addWidget(self._drop)

        btn_br = QPushButton(
            "\u6d4f\u89c8\u89c6\u9891\u6587\u4ef6")
        btn_br.clicked.connect(self._browse)
        root.addWidget(btn_br)

        self._info = QLabel("")
        self._info.setStyleSheet(
            "font-size: 13px; color: #00b4ff; "
            "font-weight: 600; "
            "background: transparent;")
        root.addWidget(self._info)

        # Preview
        self._pv = QFrame()
        self._pv.setStyleSheet(
            "QFrame { background: #000; "
            "border-radius: 8px; }")
        pv_l = QVBoxLayout(self._pv)
        pv_l.setContentsMargins(0, 0, 0, 0)

        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._vw = QVideoWidget()
        self._vw.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        self._vw.setMinimumHeight(180)
        self._vw.setStyleSheet("background: #000;")
        self._player.setVideoOutput(self._vw)
        pv_l.addWidget(self._vw)
        root.addWidget(self._pv, 1)

        self._player.positionChanged.connect(
            self._on_pos)
        self._player.durationChanged.connect(
            self._on_dur)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self._btn_play = QPushButton("\u25b6")
        self._btn_play.setFixedSize(40, 40)
        self._btn_play.setStyleSheet(
            "QPushButton { background: #00b4ff; "
            "color: #080c14; border: none; "
            "border-radius: 20px; font-size: 16px;"
            " font-weight: bold; }"
            "QPushButton:hover {"
            " background: #00c8ff; }")
        self._btn_play.clicked.connect(
            self._toggle_play)
        ctrl.addWidget(self._btn_play)

        self._pos_lbl = QLabel("00:00.00")
        self._pos_lbl.setStyleSheet(
            "font-family: 'Consolas'; "
            "font-size: 14px; "
            "font-weight: 700; color: #e8edf5; "
            "background: transparent;")
        ctrl.addWidget(self._pos_lbl)
        ctrl.addStretch()

        self._btn_split = GlowButton(
            "S \u526a\u5207", "#ff3b5c")
        self._btn_split.setFixedWidth(100)
        self._btn_split.clicked.connect(
            self._do_split)
        ctrl.addWidget(self._btn_split)

        self._btn_del = QPushButton(
            "Del \u5220\u9664")
        self._btn_del.setObjectName("dangerBtn")
        self._btn_del.setFixedWidth(100)
        self._btn_del.clicked.connect(
            self._do_delete)
        ctrl.addWidget(self._btn_del)

        self._btn_fs = QPushButton("\u26f6")
        self._btn_fs.setFixedSize(36, 36)
        self._btn_fs.setStyleSheet(
            "QPushButton { background: #1a2744; "
            "color: #8b99b0; "
            "border: 1px solid #2a3a5c; "
            "border-radius: 6px; "
            "font-size: 16px; }"
            "QPushButton:hover { color: #e8edf5; }")
        self._btn_fs.clicked.connect(
            self._toggle_fs)
        ctrl.addWidget(self._btn_fs)

        for txt, fn in [
            ("+", lambda: self._tl.zoom_in()),
            ("\u2212",
             lambda: self._tl.zoom_out())]:
            b = QPushButton(txt)
            b.setFixedSize(30, 30)
            b.setStyleSheet(
                "QPushButton { background: #1a2744;"
                " color: #e8edf5; "
                "border: 1px solid #2a3a5c; "
                "border-radius: 6px; "
                "font-size: 14px; "
                "font-weight: bold; }")
            b.clicked.connect(fn)
            ctrl.addWidget(b)

        self._dur_lbl = QLabel("00:00.00")
        self._dur_lbl.setStyleSheet(
            "font-family: 'Consolas'; "
            "font-size: 14px; "
            "color: #8b99b0; "
            "background: transparent;")
        ctrl.addWidget(self._dur_lbl)
        root.addLayout(ctrl)

        # Timeline
        self._tl = TimelineWidget()
        self._tl.cursor_moved.connect(
            self._on_cursor)
        self._tl.segments_changed.connect(
            self._refresh_table)
        root.addWidget(self._tl)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["#", "\u5f00\u59cb",
             "\u7ed3\u675f", "\u65f6\u957f"])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, 4):
            hdr.setSectionResizeMode(
                i,
                QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger
            .NoEditTriggers)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior
            .SelectRows)
        self._table.verticalHeader().setVisible(
            False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setMaximumHeight(140)
        self._table.setStyleSheet("""
            QTableWidget { background: #0b1120;
            border: 1px solid #1a2744;
            border-radius: 8px; }
            QTableWidget::item {
                padding: 4px; color: #e8edf5; }
            QTableWidget::item:alternate {
                background: #111a2e; }
            QTableWidget::item:selected {
                background: #1a2744; }
            QHeaderView::section {
                background: #162038;
                color: #8b99b0;
                border: none;
                border-bottom: 1px solid #1a2744;
                padding: 6px; font-size: 11px;
                font-weight: 600; }
        """)
        self._table.cellClicked.connect(
            self._on_table)
        root.addWidget(self._table)

        # ── Export bar with progress ──
        exp = QVBoxLayout()
        exp.setSpacing(4)

        # Progress bar row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(8)

        self._prog_bar = QProgressBar()
        self._prog_bar.setRange(0, 100)
        self._prog_bar.setValue(0)
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setFixedHeight(8)
        self._prog_bar.setStyleSheet("""
            QProgressBar {
                background: #1a2744;
                border: none;
                border-radius: 4px; }
            QProgressBar::chunk {
                background: #00e68a;
                border-radius: 4px; }
        """)
        self._prog_bar.setVisible(False)
        prog_row.addWidget(self._prog_bar, 1)

        self._pct_lbl = QLabel("")
        self._pct_lbl.setFixedWidth(42)
        self._pct_lbl.setStyleSheet(
            "font-family: 'Consolas'; "
            "font-size: 12px; font-weight: 700; "
            "color: #00e68a; "
            "background: transparent;")
        prog_row.addWidget(self._pct_lbl)
        exp.addLayout(prog_row)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        self._prog = QLabel("")
        self._prog.setStyleSheet(
            "font-size: 12px; color: #8b99b0; "
            "background: transparent;")
        status_row.addWidget(self._prog)

        self._eta_lbl = QLabel("")
        self._eta_lbl.setStyleSheet(
            "font-size: 12px; color: #8b99b0; "
            "background: transparent;")
        status_row.addWidget(self._eta_lbl)

        status_row.addStretch()

        self._btn_cancel = QPushButton(
            "\u53d6\u6d88")
        self._btn_cancel.setObjectName("dangerBtn")
        self._btn_cancel.setFixedWidth(70)
        self._btn_cancel.setVisible(False)
        self._btn_cancel.clicked.connect(
            self._cancel_export)
        status_row.addWidget(self._btn_cancel)

        self._btn_exp = GlowButton(
            "Ctrl+E \u5bfc\u51fa", "#00e68a")
        self._btn_exp.setFixedWidth(140)
        self._btn_exp.clicked.connect(
            self._export)
        status_row.addWidget(self._btn_exp)
        exp.addLayout(status_row)

        root.addLayout(exp)

    def _bind(self):
        QShortcut(QKeySequence(
            Qt.Key.Key_Space), self
        ).activated.connect(self._toggle_play)
        QShortcut(QKeySequence(
            Qt.Key.Key_S), self
        ).activated.connect(self._do_split)
        QShortcut(QKeySequence(
            Qt.Key.Key_Delete), self
        ).activated.connect(self._do_delete)
        QShortcut(QKeySequence(
            "Ctrl+E"), self
        ).activated.connect(self._export)

    # ═══════════════════════════════════════
    #  Load
    # ═══════════════════════════════════════

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "\u9009\u62e9\u89c6\u9891", "",
            "Video (*.mp4 *.mkv *.flv "
            "*.mov *.ts);;All (*)")
        if p:
            self._load_video(p)

    def _load_video(self, path):
        if not os.path.isfile(path):
            return
        self._video_path = path
        self._drop.setVisible(False)
        self._info.setText(
            "\u52a0\u8f7d: {}...".format(
                os.path.basename(path)))
        self._player.setSource(
            QUrl.fromLocalFile(path))
        self._loader = _DurationLoader(path)
        self._loader.done.connect(self._on_loaded)
        self._loader.start()

    def _on_loaded(self, path, dur):
        if path != self._video_path:
            return
        self._duration = dur
        self._info.setText(
            "\u89c6\u9891: {}  |  {}".format(
                os.path.basename(path),
                _fmt(dur)))
        self._dur_lbl.setText(_fmt(dur))
        self._tl.set_duration(dur)
        self._refresh_table()

    # ═══════════════════════════════════════
    #  Playback
    # ═══════════════════════════════════════

    def _toggle_play(self):
        if not self._video_path:
            return
        if (self._player.playbackState()
                == QMediaPlayer.PlaybackState
                .PlayingState):
            self._player.pause()
            self._btn_play.setText("\u25b6")
        else:
            self._player.play()
            self._btn_play.setText("\u23f8")

    def _on_pos(self, pos):
        sec = pos / 1000.0
        self._pos_lbl.setText(_fmt(sec))
        self._tl.set_cursor(sec)

    def _on_dur(self, dur):
        if self._duration == 0:
            self._duration = dur / 1000.0
            self._dur_lbl.setText(
                _fmt(self._duration))
            if not self._tl._segments:
                self._tl.set_duration(
                    self._duration)
                self._refresh_table()

    def _on_cursor(self, sec):
        self._pos_lbl.setText(_fmt(sec))
        self._player.setPosition(int(sec * 1000))

    # ═══════════════════════════════════════
    #  Split / Delete
    # ═══════════════════════════════════════

    def _do_split(self):
        if not self._video_path:
            return
        r = self._tl.split_at_cursor()
        if r >= 0:
            self._tl.select_at(r)
            self._refresh_table()

    def _do_delete(self):
        if not self._video_path:
            return
        sel = self._table.currentRow()
        if sel >= 0:
            self._tl.select_at(sel)
        if self._tl._selected >= 0:
            self._tl.delete_selected()
            self._refresh_table()

    # ═══════════════════════════════════════
    #  Fullscreen
    # ═══════════════════════════════════════

    def _toggle_fs(self):
        if not self._fullscreen:
            self._pv.setMinimumHeight(9999)
            self._pv.setMaximumHeight(9999)
            self._btn_fs.setText("\u2716")
            self._fullscreen = True
        else:
            self._pv.setMinimumHeight(0)
            self._pv.setMaximumHeight(9999)
            self._btn_fs.setText("\u26f6")
            self._fullscreen = False

    # ═══════════════════════════════════════
    #  Table
    # ═══════════════════════════════════════

    def _refresh_table(self):
        segs = self._tl.get_segments()
        self._table.setRowCount(len(segs))
        for i, (s, e) in enumerate(segs):
            n = QTableWidgetItem(str(i + 1))
            n.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 0, n)
            self._table.setItem(
                i, 1,
                QTableWidgetItem(_fmt(s)))
            self._table.setItem(
                i, 2,
                QTableWidgetItem(_fmt(e)))
            d = QTableWidgetItem(_fmt(e - s))
            d.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 3, d)

    def _on_table(self, row, col):
        self._tl.select_at(row)

    # ═══════════════════════════════════════
    #  Export (threaded + progress)
    # ═══════════════════════════════════════

    def _export(self):
        if not self._video_path:
            return
        if (self._exporter
                and self._exporter.isRunning()):
            return

        segs = self._tl.get_segments()
        if not segs:
            QMessageBox.information(
                self, "\u63d0\u793a",
                "\u8bf7\u5148\u526a\u5207\u89c6\u9891")
            return

        output_dir = ""
        if self.settings:
            output_dir = self.settings.get(
                "output_dir", "")
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "\u9009\u62e9\u8f93\u51fa\u76ee\u5f59")
        if not output_dir:
            return

        if not self._ffmpeg:
            self._ffmpeg = _find_ffmpeg()

        base = os.path.splitext(
            os.path.basename(
                self._video_path))[0]

        # UI: exporting state
        self._btn_exp.setVisible(False)
        self._btn_cancel.setVisible(True)
        self._prog_bar.setVisible(True)
        self._prog_bar.setValue(0)
        self._pct_lbl.setText("0%")
        self._prog.setText(
            "\u542f\u52a8\u5bfc\u51fa...")
        self._eta_lbl.setText("")

        self._exporter = _ExportWorker(
            self._video_path, segs, output_dir,
            base, self._ffmpeg)
        self._exporter.progress.connect(
            self._on_exp_progress)
        self._exporter.finished.connect(
            self._on_exp_done)
        self._exporter.start()

    def _cancel_export(self):
        if self._exporter:
            self._exporter.cancel()
            self._prog.setText(
                "\u6b63\u5728\u53d6\u6d88...")
            self._eta_lbl.setText("")

    def _on_exp_progress(self, pct, msg, detail):
        self._prog_bar.setValue(pct)
        self._pct_lbl.setText(
            "{}%".format(pct))
        self._prog.setText(msg)
        if detail:
            self._eta_lbl.setText(detail)

    def _on_exp_done(self, clips):
        self._btn_exp.setVisible(True)
        self._btn_cancel.setVisible(False)

        if clips:
            self._prog_bar.setValue(100)
            self._pct_lbl.setText("100%")
            self._prog.setText(
                "\u2705 \u5b8c\u6210! {} "
                "\u4e2a\u6587\u4ef6".format(
                    len(clips)))
            self._eta_lbl.setText("")
            out_dir = os.path.dirname(clips[0])
            if (os.name == "nt"
                    and os.path.isdir(out_dir)):
                os.startfile(out_dir)
        else:
            self._prog_bar.setValue(0)
            self._pct_lbl.setText("")
            self._prog.setText(
                "\u274c \u5bfc\u51fa\u5931\u8d25")
            self._eta_lbl.setText("")

    # ═══════════════════════════════════════
    #  Keyboard
    # ═══════════════════════════════════════

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            k = event.key()
            cur = self._tl.get_cursor()
            if k == Qt.Key.Key_Left:
                self._tl.set_cursor(
                    max(0, cur - 2))
                self._on_cursor(
                    self._tl.get_cursor())
                return True
            elif k == Qt.Key.Key_Right:
                self._tl.set_cursor(
                    min(self._duration, cur + 2))
                self._on_cursor(
                    self._tl.get_cursor())
                return True
            elif k == Qt.Key.Key_Home:
                self._tl.set_cursor(0)
                self._on_cursor(0)
                return True
            elif k == Qt.Key.Key_End:
                self._tl.set_cursor(
                    self._duration)
                self._on_cursor(self._duration)
                return True
        return super().eventFilter(obj, event)
