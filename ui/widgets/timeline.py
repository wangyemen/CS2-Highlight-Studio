"""
Timeline Widget - simplified segment-based editing (JianYing style)
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush


class TimelineWidget(QWidget):
    cursor_moved = pyqtSignal(float)
    segments_changed = pyqtSignal()
    segment_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setMaximumHeight(200)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._duration = 1.0
        self._cursor = 0.0
        self._segments = []       # [(start, end, color), ...]
        self._selected = -1

        self._drag = None
        self._drag_idx = -1
        self._drag_start = 0.0
        self._drag_orig = (0.0, 0.0)

        self._zoom = 1.0
        self._scroll = 0.0

        self._bg = QColor("#080c14")
        self._track = QColor("#111a2e")
        self._grid1 = QColor("#1a2744")
        self._grid2 = QColor("#223050")
        self._cur_c = QColor("#00b4ff")
        self._txt = QColor("#4a5c78")
        self._txt2 = QColor("#8b99b0")
        self._split_c = QColor("#ff3b5c")

        self._seg_colors = [
            QColor("#00b4ff"), QColor("#00e68a"),
            QColor("#ff9f43"), QColor("#8b5cf6"),
            QColor("#ffd93d"), QColor("#ff3b5c"),
            QColor("#00b4ff"), QColor("#00e68a"),
        ]

    # ═══════════════════════════════════════
    #  Public API
    # ═══════════════════════════════════════

    def set_duration(self, seconds):
        self._duration = max(0.1, seconds)
        self._cursor = 0.0
        self._segments = [(0.0, self._duration,
                           self._seg_colors[0])]
        self._selected = -1
        self._zoom = 1.0
        self._scroll = 0.0
        self.segments_changed.emit()
        self.update()

    def set_cursor(self, seconds):
        self._cursor = max(0, min(seconds, self._duration))
        self.update()

    def get_cursor(self):
        return self._cursor

    def get_segments(self):
        return [(s, e) for s, e, _ in self._segments]

    def set_segments(self, segs):
        self._segments = []
        for i, (s, e) in enumerate(segs):
            c = self._seg_colors[i % len(self._seg_colors)]
            self._segments.append((s, e, c))
        self._selected = -1
        self.segments_changed.emit()
        self.update()

    def split_at_cursor(self):
        """Split the segment under cursor into two."""
        c = self._cursor
        for i, (ss, se, col) in enumerate(self._segments):
            if ss < c < se - 0.05:
                old = list(self._segments)
                left = (ss, c, old[i][2])
                right = (c, se,
                         self._seg_colors[
                             (i + 1) % len(self._seg_colors)])
                self._segments.pop(i)
                self._segments.insert(i, left)
                self._segments.insert(i + 1, right)
                self._selected = i + 1
                self.segments_changed.emit()
                self.update()
                return i + 1
        return -1

    def delete_selected(self):
        if 0 <= self._selected < len(self._segments):
            self._segments.pop(self._selected)
            self._selected = min(
                self._selected, len(self._segments) - 1)
            self.segments_changed.emit()
            self.update()

    def select_at(self, index):
        if 0 <= index < len(self._segments):
            self._selected = index
            self.update()

    def clear(self):
        self._segments.clear()
        self._selected = -1
        self.segments_changed.emit()
        self.update()

    def zoom_in(self):
        self._zoom = min(20.0, self._zoom * 1.4)
        self.update()

    def zoom_out(self):
        self._zoom = max(0.3, self._zoom / 1.4)
        self.update()

    # ═══════════════════════════════════════
    #  Coords
    # ═══════════════════════════════════════

    def _mx(self):
        return 20

    def _ty(self):
        return 32

    def _th(self):
        return max(44, self.height() - 64)

    def _vw(self):
        return self.width() - 40

    def _vr(self):
        vw = self._vw()
        spx = self._duration / (vw * self._zoom)
        return self._scroll, self._scroll + vw * spx

    def _s2x(self, sec):
        vw = self._vw()
        s0, s1 = self._vr()
        if s1 <= s0:
            return self._mx()
        return int(self._mx() + (sec - s0) / (s1 - s0) * vw)

    def _x2s(self, x):
        vw = self._vw()
        s0, s1 = self._vr()
        if vw <= 0:
            return 0.0
        return s0 + (x - self._mx()) / vw * (s1 - s0)

    def _fmt_t(self, t):
        t = max(0, t)
        m = int(t) // 60
        s = t - m * 60
        return "{:02d}:{:04.1f}".format(m, s)

    def _grid_step(self, total, width):
        for st in [0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300]:
            if total / st < width / 80:
                return st
        return 300

    # ═══════════════════════════════════════
    #  Paint
    # ═══════════════════════════════════════

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mx = self._mx()
        vw = self._vw()
        ty = self._ty()
        th = self._th()

        p.fillRect(0, 0, w, h, self._bg)
        p.fillRect(mx, ty, vw, th, self._track)

        s0, s1 = self._vr()
        total = s1 - s0
        step = self._grid_step(total, vw)

        # Grid
        t = max(0, int(s0 / step) * step)
        while t <= s1:
            x = self._s2x(t)
            if mx <= x <= mx + vw:
                major = abs(t % (step * 5)) < step * 0.01
                p.setPen(QPen(
                    self._grid2 if major else self._grid1, 1))
                p.drawLine(x, ty, x, ty + th)
                if major or total < 30:
                    p.setPen(self._txt)
                    p.setFont(QFont("Consolas", 8))
                    p.drawText(x + 2, ty - 4, self._fmt_t(t))
            t += step

        # Segments
        for i, (ss, se, color) in enumerate(self._segments):
            x1 = max(mx, self._s2x(ss))
            x2 = min(mx + vw, self._s2x(se))
            if x2 <= x1:
                continue
            rect = QRect(x1, ty + 2, x2 - x1, th - 4)

            c = QColor(color)
            if i != self._selected:
                c.setAlpha(130)
            p.fillRect(rect, c)

            bc = (QColor("#ffffff") if i == self._selected
                  else QColor(color))
            bc.setAlpha(240 if i == self._selected else 60)
            p.setPen(QPen(bc, 2 if i == self._selected else 1))
            p.drawRect(rect)

            # Label
            if x2 - x1 > 25:
                p.setPen(QColor("#ffffff"))
                p.setFont(QFont("Exo 2", 8, QFont.Weight.Bold))
                p.drawText(
                    QRect(x1 + 4, ty + 4,
                          x2 - x1 - 8, th - 8),
                    Qt.AlignmentFlag.AlignCenter,
                    "{:.1f}s".format(se - ss))

        # Cursor
        cx = self._s2x(self._cursor)
        if mx <= cx <= mx + vw:
            p.setPen(QPen(self._cur_c, 2))
            p.drawLine(cx, ty - 10, cx, ty + th + 10)
            p.setBrush(QBrush(self._cur_c))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(
                QPoint(cx - 5, ty - 10),
                QPoint(cx + 5, ty - 10),
                QPoint(cx, ty))

            # Split indicator (red dashed line preview)
            p.setPen(QPen(self._split_c, 1, Qt.PenStyle.DashLine))
            p.drawLine(cx, ty, cx, ty + th)

        # Bottom
        p.setPen(self._cur_c)
        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        p.drawText(mx, h - 4, self._fmt_t(self._cursor))
        p.setPen(self._txt2)
        p.setFont(QFont("Exo 2", 9))
        cnt = len(self._segments)
        p.drawText(mx + 100, h - 4,
                   "{} \u6bb5  |  \u603b\u8ba1 {}".format(
                       cnt, self._fmt_t(self._duration)))
        p.end()

    # ═══════════════════════════════════════
    #  Mouse
    # ═══════════════════════════════════════

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.position().x()
        y = event.position().y()
        ty = self._ty()
        th = self._th()
        vw = self._vw()

        in_track = (self._mx() <= x <= self._mx() + vw
                    and ty <= y <= ty + th)

        if not in_track:
            self._drag = "cursor"
            self._cursor = max(0,
                min(self._x2s(x), self._duration))
            self.cursor_moved.emit(self._cursor)
            self.update()
            return

        sec = self._x2s(x)

        # Hit a segment
        hit = False
        for i in range(len(self._segments) - 1, -1, -1):
            ss, se, _ = self._segments[i]
            if ss <= sec <= se:
                self._selected = i
                self._drag = "move"
                self._drag_idx = i
                self._drag_orig = (ss, se)
                self._drag_start = sec
                self.segment_selected.emit(i)
                hit = True
                self.update()
                break

        if not hit:
            self._drag = "cursor"
            self._cursor = max(0, min(sec, self._duration))
            self.cursor_moved.emit(self._cursor)
            self.update()

    def mouseMoveEvent(self, event):
        x = event.position().x()
        sec = self._x2s(x)

        if self._drag == "cursor":
            self._cursor = max(0,
                min(sec, self._duration))
            self.cursor_moved.emit(self._cursor)
            self.update()

        elif self._drag == "move":
            delta = sec - self._drag_start
            os_, oe = self._drag_orig
            dur = oe - os_
            ns = max(0,
                min(os_ + delta, self._duration - dur))
            self._segments[self._drag_idx] = (
                ns, ns + dur,
                self._segments[self._drag_idx][2])
            self.segments_changed.emit()
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag = None
        self._drag_idx = -1
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Plus:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)
