# pylint: disable=invalid-name, comparison-with-callable, using-constant-test
import os
from functools import lru_cache
from typing import TYPE_CHECKING

from PyQt5.QtCore import (  # type: ignore  # pylint: disable=no-name-in-module
    QEvent,
    QRect,
    Qt,
)
from PyQt5.QtGui import (  # pylint: disable=no-name-in-module
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt5.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from .. import Color, Intersection, Pos, stone
from . import BASE_DIR, GUIMode

if TYPE_CHECKING:
    from .boardwidget import BoardWidget, InsParams
    from .gamewindow import GameWindow  # type: ignore


@lru_cache()
def get_pixmap(status: Color) -> QPixmap | None:
    if status == Color.BLACK:
        path = "gui/imgs/black.png"
    elif status == Color.WHITE:
        path = "gui/imgs/white.png"
    else:
        return None
    return QPixmap(QImage(os.path.join(BASE_DIR, path)))


class IntersectionWidget(QWidget):
    """Visual representation of a intersection in a go board"""

    def __init__(self, parent: "BoardWidget", board_pos: Pos, is_hoshi: bool):
        super().__init__(parent)
        self.board_pos: Pos = board_pos
        self.stone: stone.Stone | None = None
        self.controller: "GameWindow" = parent.parent()
        self.is_hoshi = is_hoshi
        self._is_current = None
        self._hover = False
        self.installEventFilter(self)
        self.inter: Intersection | None = None

    def mousePressEvent(self, event):
        self.controller.inter_clicked(self, is_rightclick=event.button() == Qt.RightButton)
        self._hover = False

    def draw_number(self, painter, params):
        self.draw_char(str(len(self.stone.annos.numbers)), painter, params)

    def draw_char(self, txt, painter, params, color=None):
        font = painter.font()
        font.setPixelSize(int(params.font_height))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color or QColor("green"))
        painter.drawText(QRect(0, 0, params.size, params.size), Qt.AlignCenter, txt)

    def draw_x(self, painter, params, color=None):
        self.draw_char("X", painter, params)

    def draw_winrate(self, info, painter, params):
        font = painter.font()
        font.setPixelSize(int(params.size / (len(info[0]) / 1.4)))
        fwidth = 4
        perc = float(info[0])
        val = perc * 2.5
        green = int(val)
        red = int(255 - val)
        blue = 255 - abs(red - green)  # 2*455 - red - green)  # int(abs(125 - val / 2))  # int(red)
        painter.setBrush(QColor(red, green, blue))
        painter.drawEllipse(fwidth, fwidth, params.size - (fwidth * 2), params.size - (fwidth * 2))
        fg = QColor(
            abs(int(122 - (red * 0.3))), abs(122 - green), (abs(122 - blue))
        )  # abs(122 - blue)))
        font = painter.font()
        txt = info[0]
        font.setPixelSize(int(params.size / (len(txt) / 1.4)))
        painter.setFont(font)
        painter.setPen(fg)
        painter.drawText(
            QRect(0, params.font_bottom, params.size, params.size),
            Qt.AlignCenter,
            txt,
        )
        txt = info[1]
        txt = txt[: min(4, len(txt))]
        font = painter.font()
        psize = int(params.small_size / (len(txt) / 2))
        font.setPixelSize(psize)
        painter.setFont(font)
        painter.drawText(
            QRect(psize, int(psize * 0.7), params.small_size, params.size),
            Qt.AlignCenter,
            txt,
        )

    def draw_circle(self, painter, params):
        fwidth = 4
        pen = QPen(QColor("green"), 4)
        painter.setPen(pen)
        painter.drawEllipse(fwidth, fwidth, params.size - (fwidth * 2), params.size - (fwidth * 2))

    def draw_triangle(self, painter, params):
        path = QPainterPath()
        fwidth = 4
        size = params.size - (fwidth // 2)
        path.moveTo(fwidth, size)
        path.lineTo(size // 2, fwidth)
        path.lineTo(size, size)
        path.lineTo(fwidth, size)
        pen = QPen(QColor("green"), fwidth)
        painter.strokePath(path, pen)

    def draw_square(self, painter, params):
        path = QPainterPath()
        fwidth = 4
        size = params.size - (fwidth // 2)
        path.moveTo(fwidth, fwidth)
        path.lineTo(fwidth, size)
        path.lineTo(size, size)
        path.lineTo(size, fwidth)
        path.lineTo(fwidth, fwidth)
        pen = QPen(QColor("green"), fwidth)
        painter.strokePath(path, pen)

    def draw_owned(self, color, painter, params):
        assert (owned_pixmap := get_pixmap(color))
        painter.setOpacity(0.5)
        painter.drawPixmap(
            QRect(
                params.small_pos,
                params.small_pos,
                params.small_size,
                params.small_size,
            ),
            owned_pixmap,
        )
        painter.setOpacity(1)

    def draw_dimmed(self, painter: QPainter, params: "InsParams"):
        painter.setBrush(Qt.gray)
        # self.draw_char(info[0], painter, params, fg)
        # self.draw_char(info[0], painter, params, fg)
        painter.setOpacity(0.8)
        painter.fillRect(0, 0, params.size, params.size, painter.brush())
        painter.setOpacity(1)

    def paintEvent(self, _):
        """Draw"""
        if not self.controller.curr_action_result:
            return
        self.inter = self.controller.curr_action_result.board.intersection(self.board_pos)
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHints(
            painter.Antialiasing | painter.SmoothPixmapTransform | painter.HighQualityAntialiasing
        )
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor("black"))
        painter.setPen(pen)
        params: "InsParams" = self.parent().ins_params
        if self.controller.curr_action_result.stone_result:
            self.stone = self.controller.curr_action_result.stone_result.stone
        analyzed_variation = self.stone.annos.progress.get(self.board_pos)

        if self.is_hoshi:
            brush = painter.brush()
            size = params.hoshi_size
            pos = params.hoshi_pos
            painter.setBrush(QColor("black"))
            painter.drawEllipse(pos, pos, size, size)
            painter.setBrush(brush)

        stone_pixmap = get_pixmap(self.inter.color)
        if (not stone_pixmap) and (rate := self.stone.annos.winrates.get(self.board_pos)):
            if not self.parent().show_analyzed_variation:
                self.draw_winrate(rate, painter, params)

        if stone_pixmap:
            painter.drawPixmap(
                QRect(
                    params.stone_pos,
                    params.stone_pos,
                    params.stone_size,
                    params.stone_size,
                ),
                stone_pixmap,
            )
            if self.board_pos == self.stone.pos:
                painter.setBrush(QColor("red"))
                painter.drawEllipse(
                    params.small_pos,
                    params.small_pos,
                    params.small_size,
                    params.small_size,
                )
        elif self.controller.gui_mode in (GUIMode.EDIT, GUIMode.PLAY):
            for child in self.stone.children:
                if self.board_pos == child.pos:
                    break
            else:
                child = None
            if child:
                child_pixmap = get_pixmap(child.color)
                painter.setOpacity(0.5)
                painter.drawPixmap(
                    QRect(
                        params.small_pos,
                        params.small_pos,
                        params.small_size,
                        params.small_size,
                    ),
                    child_pixmap,
                )
                painter.setOpacity(1)
        if self.controller.gui_mode == GUIMode.EDIT:
            if marker := self.stone.annos.markers.get(self.board_pos):
                getattr(self, f"draw_{marker.value}")(painter, params)
            if color := self.stone.annos.owned.get(self.board_pos):
                self.draw_owned(color, painter, params)
            elif txt := self.stone.annos.chars.get(self.board_pos):
                self.draw_char(txt, painter, params)
            elif txt := self.stone.annos.numbers.get(self.board_pos):
                self.draw_char(txt, painter, params)
            #       pass
        if (not stone_pixmap) and self._hover:
            next_color = (
                self.controller.curr_action_result.stone_result.next_color
                if self.controller.curr_action_result.stone_result
                else None
            )
            if next_color:
                hover_pixmap = get_pixmap(next_color)
                painter.setOpacity(0.8)
                painter.drawPixmap(
                    QRect(
                        params.stone_pos,
                        params.stone_pos,
                        params.stone_size,
                        params.stone_size,
                    ),
                    hover_pixmap,
                )
        if analyzed_variation:
            index, color = analyzed_variation
            assert (vari_pixmap := get_pixmap(color))
            painter.setOpacity(0.8)
            painter.drawPixmap(
                QRect(
                    params.stone_pos,
                    params.stone_pos,
                    params.stone_size,
                    params.stone_size,
                ),
                vari_pixmap,
            )
            painter.setOpacity(1)
            color = QColor(10 * index, 255, 255 - 20 * index)
            self.draw_char(str(index), painter, params, color)
            # self._hover = False
        if self.controller.gui_mode == GUIMode.COUNT:
            if self.inter.owner:
                self.draw_owned(self.inter.owner, painter, params)
            #    assert (owned_pixmap := get_pixmap(self.inter.owner))
            #    painter.setOpacity(0.5)
            #    painter.drawPixmap(
            #        QRect(
            #            params.small_pos,
            #            params.small_pos,
            #            params.small_size,
            #            params.small_size,
            #        ),
            #        owned_pixmap,
            #    )
            #    painter.setOpacity(1)
        self._hover = False
        painter.end()

    def eventFilter(self, _object, event):
        if self.inter and self.inter.color == Color.EMPTY:  # and not self.controller.is_annotating:
            type_ = event.type()

            # stone = self.controller.curr_action_result.stone
            analyzed_variation_stones = []
            if rate := self.stone.annos.winrates.get(self.board_pos):
                analyzed_variation_stones = rate[2]

            if (
                type_
                == QEvent.Enter
                # and not self.controller.bar.inner.boxes["EditBox"].decogroup.checkedButton()
            ):
                self._hover = True
                if analyzed_variation_stones:
                    color = self.controller.curr_action_result.next_color
                    for index, pos in enumerate(analyzed_variation_stones):
                        self.stone.annos.progress[pos] = index + 1, color
                        color = Color.WHITE if color == Color.BLACK else Color.BLACK
                    self.parent().show_analyzed_variation = True
                    self.parent().repaint()
                else:
                    self.repaint()

                    # print("VR", stone.annos.progress[self.board_pos])
                # if not self.controller.is_annotating:

                # .annos.winrates.get(self.board_pos)):
                return True

            if (
                type_
                == QEvent.Leave
                # and not self.controller.bar.inner.boxes["EditBox"].decogroup.checkedButton()
            ):
                # if not self.controller.is_annotating:
                self._hover = False
                self.parent().show_analyzed_variation = False
                self.repaint()
                if self.stone.annos.progress:
                    self.stone.annos.progress.clear()
                    self.parent().repaint()
                return True

        return False
