# pylint: disable=invalid-name  # because qt
import math
import os
from itertools import permutations
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import (  # py2lint: disable=no-name-in-module
    QLineF,
    QPointF,
    QRect,
    Qt,
)
from PyQt6.QtGui import (  # pylint: disable=no-name-in-module; QBrush,
    QColor,
    QImage,
    QPainter,
    QPolygonF,
)
from PyQt6.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from pygoban import BaseReceiver, Pos, results

from . import BASE_DIR, GameUI, InsParams
from .intersections import IntersectionWidget

# check
if TYPE_CHECKING:
    from .gamewidget import GameWidget

COORDS = [chr(i) for i in list(range(97, 117))]


def _hoshi_combis(singlecoords):
    return list(permutations((singlecoords), 2)) + [(i, i) for i in singlecoords]


HOSHIS = {
    9: _hoshi_combis((2, 6)) + [(4, 4)],
    13: _hoshi_combis((3, 6, 9)),
    19: _hoshi_combis((3, 9, 15)),
}


class BoardWidget(QWidget):

    def __init__(self, parent: GameUI, boardsize: int):
        super().__init__(parent=parent)
        self.bgimage = QImage(os.path.join(BASE_DIR, "gui/imgs/shinkaya.jpg"))
        self.boardsize = boardsize
        self.boardwidth = 0
        self.borderspace = 0
        self.intersections: dict[Pos, IntersectionWidget] = {}
        self.boardrange = range(self.boardsize)
        self.current_in = None  # "Active" intersection
        # self.boardupdate_signal.connect(self.update_board)
        self.ins_params = InsParams()
        self.create_intersections()
        self.setAutoFillBackground(True)

    def create_intersections(self):
        assert not self.intersections
        hoshis = HOSHIS.get(self.boardsize, [])
        for x, y in [(x, y) for x in self.boardrange for y in self.boardrange]:
            cx, cy = x, y  # rotate(x, y, self.boardsize)
            pos = Pos(cx, cy)
            is_hoshi = (cx, cy) in hoshis
            iwidget = IntersectionWidget(self, pos, is_hoshi)
            iwidget.setParent(self)
            self.intersections[pos] = iwidget

        self._resize()

    def _resize(self):
        ins = self.intersections
        if not ins:
            return

        self.borderspace = int(self.width() / self.boardsize)
        intersize = int((self.width() - 2 * self.borderspace) / self.boardsize)
        if intersize != self.ins_params.size:
            self.calc_intersize(intersize)
        self.boardwidth = self.ins_params.size * self.boardsize
        if self.intersections:
            for x in self.boardrange:
                for y in self.boardrange:
                    pos = Pos(x, y)
                    inter = self.intersections[pos]
                    inter.setGeometry(
                        x * intersize + self.borderspace,
                        y * intersize + self.borderspace,
                        intersize,
                        intersize,
                    )
                    inter.show()

    def calc_intersize(self, size):
        """Calc for one - use for all"""
        params = self.ins_params
        params.size = size
        params.hoshi_size = size // 5
        params.hoshi_pos = (size - params.hoshi_size) // 2
        params.stone_size = int(size)
        params.font_height = int(size * 0.8)
        params.font_bottom = (params.font_height - size) // 2
        params.small_size = params.size // 2
        params.small_pos = (size - params.small_size) // 2

    def resizeEvent(self, _event):
        self._resize()

    def paintEvent(self, _event):
        """Paint a board"""
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(
            QRect(0, 0, self.width(), self.height()),
            self.bgimage,
            QRect(0, 0, 905, 898),
        )
        dist = int(self.boardwidth / self.boardsize)
        pen = painter.pen()
        pen.setColor(QColor("black"))
        pen.setWidth(1)  # if pos in (0, self.boardsize - 1) else 2)
        painter.setPen(pen)
        painter.setRenderHints(
            # painter.Antialiasing | painter.SmoothPixmapTransform | painter.HighQualityAntialiasing
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        hdist = dist // 2
        # painter.fillRect(
        #     self.borderspace,
        #     self.borderspace,
        #     self.boardwidth,
        #     self.boardwidth,  # + hdist,
        #     QBrush(Qt.green),
        # )
        for pos in self.boardrange:
            pen = painter.pen()
            firstorlast = pos == 0 or pos == self.boardsize - 1
            pen.setWidth(4 if firstorlast else 2)
            width = self.boardwidth - (1 if not firstorlast else 2)
            painter.setPen(pen)
            x = self.borderspace + pos * dist
            letter_index = pos
            if pos > 7:
                letter_index += 1
            painter.drawText(
                QRect(x, int(self.borderspace / 4), dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                COORDS[letter_index].upper(),
            )
            painter.drawText(
                QRect(x, int(self.borderspace) + self.boardwidth, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                COORDS[letter_index].upper(),
            )

            painter.drawText(
                QRect(int(self.borderspace / 4), x, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                str(self.boardsize - pos),
            )
            painter.drawText(
                QRect(int(self.borderspace) + self.boardwidth, x, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                str(self.boardsize - pos),
            )

            painter.drawLine(
                x + hdist,
                self.borderspace + hdist,
                x + hdist,
                self.borderspace + width - hdist,
            )
            painter.drawLine(
                self.borderspace + hdist,
                x + hdist,
                self.borderspace + width - hdist,
                x + hdist,
            )

        painter.end()


class BoardOverlay(QWidget, BaseReceiver):

    def __init__(self, parent: "GameWidget") -> None:
        super().__init__(parent=parent)  # pylint: disable=unexpected-keyword-arg
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.board = parent.boardwidget
        self.game_ui: GameUI = cast(GameUI, parent)
        self.game_ui.controller.add_receiver(self)
        self.events = {results.TurnDone}
        self.result: results.TurnDone | None = None
        self.startpos: Pos | None = None

    def paintEvent(self, _event):
        """Paint a board"""
        super().paintEvent(_event)

        if not self.result:
            return
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = painter.pen()
        pen.setColor(QColor("red"))
        pen.setWidth(4)  # if pos in (0, self.boardsize - 1) else 2)
        painter.setPen(pen)
        painter.setBrush(QColor("red"))

        def draw_line(pospair: tuple[Pos, Pos]) -> QLineF:
            i2 = self.board.intersections[pospair[0]]
            i1 = self.board.intersections[pospair[1]]
            pi1 = i1.pos()
            pi2 = i2.pos()
            p1 = QPointF(pi1.x(), pi1.y())
            p2 = QPointF(pi2.x(), pi2.y())
            p1.setX(p1.x() + self.board.ins_params.size / 2)
            p1.setY(p1.y() + self.board.ins_params.size / 2)
            p2.setX(p2.x() + self.board.ins_params.size / 2)
            p2.setY(p2.y() + self.board.ins_params.size / 2)
            line = QLineF(p1, p2)
            painter.drawLine(line)
            return line

        def draw_arrow(pospair: tuple[Pos, Pos]):
            arrow_size = self.board.ins_params.size // 2
            line = draw_line(pospair=pospair)
            angle = math.atan2(-line.dy(), line.dx())
            arrowP1 = line.p1() + QPointF(
                math.sin(angle + math.pi / 3) * arrow_size,
                math.cos(angle + math.pi / 3) * arrow_size,
            )
            arrowP2 = line.p1() + QPointF(
                math.sin(angle + math.pi - math.pi / 3) * arrow_size,
                math.cos(angle + math.pi - math.pi / 3) * arrow_size,
            )
            arrow_head = QPolygonF()
            arrow_head.clear()
            arrow_head << line.p1() << arrowP1 << arrowP2
            painter.drawPolygon(arrow_head)

        for pospair in self.result.node.annos.lines:
            draw_line(pospair)
        for pospair in self.result.node.annos.arrows:
            draw_arrow(pospair)
        painter.end()

    def received_turn(self, result):
        self.result = result
