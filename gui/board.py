# pylint: disable=no-name-in-module
import os
import sys
from itertools import permutations
from threading import Timer

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QColor, QImage, QPainter
from PyQt5.QtWidgets import QApplication, QWidget

from lib.controller import Controller
from lib.status import BLACK, EMPTY

from . import BASE_DIR
from .intersection import Intersection

app = QApplication(sys.argv)

COORDS = [chr(i) for i in list(range(97, 117))]


def _hoshi_combis(singlecoords):
    return list(permutations((singlecoords),2)) + [(i,i) for i in singlecoords]


HOSHIS = {
    9: _hoshi_combis((2,6)) + [(4,4)],
    13: _hoshi_combis((3,6,9)) ,
    19: _hoshi_combis((3,9,15)),
}


class GuiController(QWidget, Controller):
    def __init__(self, black, white, game, *args, **kwargs):
        super().__init__(*args, **kwargs, black=black, white=white, game=game)
        self.bgimage = QImage(os.path.join(BASE_DIR, "gui/imgs/shinkaya.jpg"))
        board = game.movetree.board
        self.boardsize = board.boardsize
        self.intersections = []
        hoshis = HOSHIS.get(self.boardsize, [])
        for x in range(self.boardsize):
            self.intersections.append([])
            for y in range(self.boardsize):
                is_hoshi = (x, y) in hoshis
                status = board[x][y]
                inter = Intersection(self, x, y, status, is_hoshi)
                self.intersections[x].append(inter)
        Timer(1, lambda : self.set_turn(BLACK, None)).start()

    def set_turn(self, color, result):
        if result:
            if not result.extra:
                self.intersections[result.y][self.boardsize - 1 - result.x].status = result.color
                for killed in result.killed:
                    self.intersections[killed[1]][self.boardsize - 1 - killed[0]].status = EMPTY
        super().set_turn(color, result)

    def get_bordersize(self):
        '''Todo'''
        bordersize = int(self.width() / self.boardsize)
        return bordersize

    def resizeEvent(self, event):
        borderspace = self.get_bordersize()
        width = (self.width() - 2 * borderspace) / self.boardsize

        for x in range(self.boardsize):
            for y in range(self.boardsize):
                inter = self.intersections[x][y]
                inter.setGeometry(
                    x * width + borderspace,
                    y * width + borderspace,
                    width, width)
        self.intersections[0][0].calc()
        self.repaint()

    def paintEvent(self, evt):  # pylint: disable=invalid-name, unused-argument
        '''Paint a board'''
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(
            QRect(0, 0, self.width(), self.height()),
            self.bgimage,
            QRect(0, 0, 905, 898)
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
                painter.Antialiasing |
                painter.SmoothPixmapTransform |
                painter.HighQualityAntialiasing)
            x = pos * dist
            painter.drawText(
                QRect(x + borderspace, borderspace / 4, dist, dist),
                Qt.AlignCenter,
                COORDS[pos].upper())

            painter.drawText(
                QRect(borderspace / 4, x + borderspace, dist, dist),
                Qt.AlignCenter, str(self.boardsize - pos))

            painter.drawLine(
                x + hdist + borderspace,
                hdist + borderspace,
                x + hdist + borderspace,
                (dist * self.boardsize - hdist) + borderspace)

            painter.drawLine(
                hdist + borderspace,
                x + hdist + borderspace,
                dist * self.boardsize - hdist + borderspace,
                x + hdist + borderspace)

        painter.end()
