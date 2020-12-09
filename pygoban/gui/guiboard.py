# pylint: disable=invalid-name
import os
from itertools import permutations

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QColor, QImage, QPainter
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from pygoban import events
from . import BASE_DIR, rotate
from .intersection import Intersection


COORDS = [chr(i) for i in list(range(97, 117))]


def _hoshi_combis(singlecoords):
    return list(permutations((singlecoords), 2)) + [(i, i) for i in singlecoords]


HOSHIS = {
    9: _hoshi_combis((2, 6)) + [(4, 4)],
    13: _hoshi_combis((3, 6, 9)),
    19: _hoshi_combis((3, 9, 15)),
}


class GuiBoard(QWidget):
    boardupdate_signal = pyqtSignal(events.Event, list)

    def __init__(self, parent, boardsize, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.bgimage = QImage(os.path.join(BASE_DIR, "gui/imgs/shinkaya.jpg"))
        self.boardsize = boardsize
        self.intersections = {}
        self.boardrange = range(self.boardsize)
        self.current_in = None  # "Active" intersection
        self.boardupdate_signal.connect(self.update_intersections)

    def update_intersections(self, result, board):
        create = not self.intersections
        hoshis = HOSHIS.get(self.boardsize, [])
        for x in self.boardrange:
            for y in self.boardrange:
                cx, cy = x, y  # rotate(x, y, self.boardsize)
                pos = (cx, cy)
                status = board[cx][cy]
                if create:
                    is_hoshi = (cx, cy) in hoshis
                    inter = Intersection(self, pos, status, is_hoshi)
                    inter.show()
                    inter.setParent(self)
                    self.intersections[pos] = inter
                else:
                    inter = self.intersections[pos]
                    inter.status = status

        if self.current_in:
            self.current_in.is_current = False
        if isinstance(result, events.CursorChanged):
            move = result.cursor
            if not move.is_empty:
                self.intersections[move.pos].is_current = True
        if create:
            self.resizeEvent(None)

    def get_bordersize(self):
        """Todo"""
        bordersize = int(self.width() / self.boardsize)
        return bordersize

    def resizeEvent(self, _event):
        borderspace = self.get_bordersize()
        width = (self.width() - 2 * borderspace) / self.boardsize
        if self.intersections:
            for x in range(self.boardsize):
                for y in range(self.boardsize):
                    pos = rotate(x, y, self.boardsize)
                    inter = self.intersections[pos]
                    # print("xY", x,y, inter)
                    # print( x * width + borderspace, y * width + borderspace, width, width)
                    inter.setGeometry(
                        x * width + borderspace, y * width + borderspace, width, width
                    )
                    # inter.update()
            self.intersections[(0, 0)].calc()
        self.repaint()

    def paintEvent(self, _event):
        """Paint a board"""
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(
            QRect(0, 0, self.width(), self.height()),
            self.bgimage,
            QRect(0, 0, 905, 898),
        )
        borderspace = self.get_bordersize()
        boardwidth = self.width() - 2 * borderspace
        dist = boardwidth / self.boardsize
        hdist = dist / 2
        for pos in range(self.boardsize):
            pen = painter.pen()
            pen.setColor(QColor("black"))
            pen.setWidth(4 if pos in (0, self.boardsize - 1) else 2)
            painter.setPen(pen)
            painter.setRenderHints(
                painter.Antialiasing
                | painter.SmoothPixmapTransform
                | painter.HighQualityAntialiasing
            )
            x = pos * dist
            painter.drawText(
                QRect(x + borderspace, borderspace / 4, dist, dist),
                Qt.AlignCenter,
                COORDS[pos].upper(),
            )

            painter.drawText(
                QRect(borderspace / 4, x + borderspace, dist, dist),
                Qt.AlignCenter,
                str(self.boardsize - pos),
            )

            painter.drawLine(
                x + hdist + borderspace,
                hdist + borderspace,
                x + hdist + borderspace,
                (dist * self.boardsize - hdist) + borderspace,
            )

            painter.drawLine(
                hdist + borderspace,
                x + hdist + borderspace,
                dist * self.boardsize - hdist + borderspace,
                x + hdist + borderspace,
            )

        painter.end()
