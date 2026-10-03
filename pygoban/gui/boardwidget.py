# pylint: disable=invalid-name  # because qt
import math
import os
from itertools import permutations
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import (
    QLineF,
    QPointF,
    QRect,
    Qt,
)
from PyQt6.QtGui import (
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

COORDS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def _column_label(index: int) -> str:
    label = ""
    while index >= 0:
        index, remainder = divmod(index, len(COORDS))
        label = COORDS[remainder] + label
        index -= 1
    return label


def _hoshi_combis(singlecoords):
    return list(permutations((singlecoords), 2)) + [(i, i) for i in singlecoords]


HOSHIS = {
    9: _hoshi_combis((2, 6)) + [(4, 4)],
    13: _hoshi_combis((3, 6, 9)),
    19: _hoshi_combis((3, 9, 15)),
}


class BoardWidget(QWidget):
    def __init__(
        self, parent: GameUI, boardsize: int, boardheight: int | None = None
    ):
        super().__init__(parent=parent)
        self.bgimage = QImage(os.path.join(BASE_DIR, "gui/imgs/shinkaya.jpg"))
        self.boardsize = boardsize
        self.boardheight = boardsize if boardheight is None else boardheight
        self.boardwidth = 0
        self.boardpixelheight = 0
        self.boardleft = 0
        self.boardtop = 0
        self.intersections: dict[Pos, IntersectionWidget] = {}
        self.boardrange_x = range(self.boardsize)
        self.boardrange_y = range(self.boardheight)
        self.current_in = None  # "Active" intersection
        self.ins_params = InsParams()
        self.create_intersections()
        self.setAutoFillBackground(True)

    def create_intersections(self):
        assert not self.intersections
        hoshis = HOSHIS.get(self.boardsize, []) if self.boardheight == self.boardsize else []
        for x, y in [(x, y) for x in self.boardrange_x for y in self.boardrange_y]:
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

        intersize = max(
            1,
            int(
                min(
                    self.width() / (self.boardsize + 2),
                    self.height() / (self.boardheight + 2),
                )
            ),
        )
        if intersize != self.ins_params.size:
            self.calc_intersize(intersize)
        self.boardwidth = self.ins_params.size * self.boardsize
        self.boardpixelheight = self.ins_params.size * self.boardheight
        self.boardleft = (self.width() - self.boardwidth) // 2
        self.boardtop = (self.height() - self.boardpixelheight) // 2
        if self.intersections:
            for x in self.boardrange_x:
                for y in self.boardrange_y:
                    pos = Pos(x, y)
                    inter = self.intersections[pos]
                    inter.setGeometry(
                        x * intersize + self.boardleft,
                        y * intersize + self.boardtop,
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

        # painter.setRenderHints(
        #     # painter.Antialiasing | painter.SmoothPixmapTransform | painter.HighQualityAntialiasing
        #     QPainter.RenderHint.Antialiasing
        #     | QPainter.RenderHint.SmoothPixmapTransform
        # )
        painter.begin(self)
        painter.drawImage(
            QRect(0, 0, self.width(), self.height()),
            self.bgimage,
            QRect(0, 0, 905, 898),
        )
        dist = self.ins_params.size
        pen = painter.pen()
        pen.setColor(QColor("black"))
        pen.setWidth(1)  # if pos in (0, self.boardsize - 1) else 2)
        painter.setPen(pen)
        hdist = dist // 2
        for pos in self.boardrange_x:
            pen = painter.pen()
            firstorlast = pos in (0, self.boardsize - 1)
            pen.setWidth(2 if firstorlast else 1)
            painter.setPen(pen)
            x = self.boardleft + pos * dist
            painter.drawText(
                QRect(x, self.boardtop - dist, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                _column_label(pos),
            )
            painter.drawText(
                QRect(x, self.boardtop + self.boardpixelheight, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                _column_label(pos),
            )
            painter.drawLine(
                x + hdist,
                self.boardtop + hdist,
                x + hdist,
                self.boardtop + self.boardpixelheight - hdist,
            )

        for pos in self.boardrange_y:
            pen = painter.pen()
            firstorlast = pos in (0, self.boardheight - 1)
            pen.setWidth(2 if firstorlast else 1)
            painter.setPen(pen)
            y = self.boardtop + pos * dist
            painter.drawText(
                QRect(self.boardleft - dist, y, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                str(self.boardheight - pos),
            )
            painter.drawText(
                QRect(self.boardleft + self.boardwidth, y, dist, dist),
                Qt.AlignmentFlag.AlignCenter,
                str(self.boardheight - pos),
            )
            painter.drawLine(
                self.boardleft + hdist,
                y + hdist,
                self.boardleft + self.boardwidth - hdist,
                y + hdist,
            )

        painter.end()


class BoardOverlay(QWidget, BaseReceiver):  # pylint: disable=abstract-method
    def __init__(self, parent: "GameWidget") -> None:
        super().__init__(parent)  # pylint: disable=too-many-function-args
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.board = parent.boardwidget
        self.game_ui: GameUI = cast(GameUI, parent)
        self.game_ui.controller.add_receiver(self)
        self.events = {results.TurnDone, results.GameResultDone}
        self.result: results.TurnDone | None = None
        self.startpos: Pos | None = None
        self.msg = ""

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

        if self.msg:
            font = painter.font()  # QFont()
            font.setPixelSize(self.height() // 8)
            painter.setFont(font)

            painter.drawText(100, 100, self.msg)

        painter.end()

    def received_turn(self, result: results.TurnDone):
        self.result = result
        self.msg = ""

    def received_result_done(self, result: results.GameResultDone):
        self.msg = result.msg
