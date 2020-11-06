# pylint: disable=invalid-name, comparison-with-callable, using-constant-test
import os

from PyQt5.QtCore import QRect, Qt, pyqtProperty, QEvent
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from pygoban.status import (
    STATUS,
    BLACK,
    WHITE,
    DEAD_BLACK,
    DEAD_WHITE,
    EMPTY,
    BLACK_LIB,
    WHITE_LIB,
)

from . import BASE_DIR, InputMode


class Intersection(QWidget):
    """Visual representation of a intersection in a go board"""

    boardsize = 9
    stone_by_status = {
        BLACK: QImage(os.path.join(BASE_DIR, "gui/imgs/black.png")),
        WHITE: QImage(os.path.join(BASE_DIR, "gui/imgs/white.png")),
        DEAD_BLACK: QImage(os.path.join(BASE_DIR, "gui/imgs/black_trans.png")),
        DEAD_WHITE: QImage(os.path.join(BASE_DIR, "gui/imgs/white_trans.png")),
    }

    current_in = None

    def __init__(self, parent, coord, status, is_hoshi):
        super().__init__(parent)
        self.controller = parent.parent()
        self.coord = coord
        self._status = status
        self.is_hoshi = is_hoshi
        self._is_current = None
        self._hover = False
        self.installEventFilter(self)

    @pyqtProperty(bool)
    def is_current(self):
        return self._is_current

    @is_current.setter
    def is_current(self, _is_current):
        if self.controller.current_in:
            self.controller.current_in._is_current = False
        self._is_current = _is_current
        self.controller.current_in = self if _is_current else None
        self.update()

    @pyqtProperty(int)
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if status != self._status:
            self._status = status
            self.update()

    def mousePressEvent(self, event):
        self.controller.inter_clicked(self)

    def draw_char(self, painter, char):
        ctrl = self.controller
        font = painter.font()
        font.setPixelSize(ctrl.ins_font_height)
        painter.setFont(font)
        painter.setPen(QColor("green"))
        painter.drawText(
            QRect(0, ctrl.ins_font_bottom, ctrl.ins_width, ctrl.ins_width),
            Qt.AlignCenter,
            char,
        )

    def paintEvent(self, _):
        """Draw"""

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHints(
            painter.Antialiasing
            | painter.SmoothPixmapTransform
            | painter.HighQualityAntialiasing
        )
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor("black"))
        painter.setPen(pen)
        ctrl = self.controller

        if self.is_hoshi:
            hosz = ctrl.ins_hoshi_size
            hosp = ctrl.ins_hoshi_pos
            painter.setBrush(QColor("black"))
            painter.drawEllipse(hosp, hosp, hosz, hosz)

        for status in (BLACK, WHITE):
            if self.coord in self.controller.game.cursor.extras.stones[status]:
                self.status = status

        stone_img = self.stone_by_status.get(self.status)
        if self.controller.game.currentcolor and self._hover and not stone_img:
            stone_img = self.stone_by_status.get(
                STATUS[self.controller.game.currentcolor.intval + 2]
            )

        if stone_img:
            pixmap = QPixmap(stone_img)
            painter.drawPixmap(
                QRect(
                    ctrl.ins_stone_pos,
                    ctrl.ins_stone_pos,
                    ctrl.ins_stone_size,
                    ctrl.ins_stone_size,
                ),
                pixmap,
            )
        if self.controller.input_mode != InputMode.COUNT:
            deco = self.controller.game.cursor.extras.decorations.get(self.coord)
            if deco:
                self.draw_char(painter, deco)
            child = self.controller.game.cursor.children.get(self.coord)

            if child and not deco:
                self.draw_char(
                    painter,
                    str(
                        tuple(self.controller.game.cursor.children.keys()).index(
                            self.coord
                        )
                        + 1
                    ),
                )

            if self.is_current:
                painter.setBrush(QColor("red"))
                painter.drawEllipse(
                    ctrl.ins_small_pos,
                    ctrl.ins_small_pos,
                    ctrl.ins_small_height,
                    ctrl.ins_small_height,
                )
        elif self.status in (BLACK_LIB, WHITE_LIB, DEAD_BLACK, DEAD_WHITE):
            stone_img = self.stone_by_status[
                BLACK if self.status in (BLACK_LIB, DEAD_WHITE) else WHITE
            ]
            pixmap = QPixmap(stone_img)
            painter.drawPixmap(
                QRect(
                    ctrl.ins_small_pos,
                    ctrl.ins_small_pos,
                    ctrl.ins_small_height,
                    ctrl.ins_small_height,
                ),
                pixmap,
            )

        painter.end()

    def calc(self):
        """Calc for one - use for all"""
        ctrl = self.controller
        width = self.width()
        ctrl.ins_width = width

        ctrl.ins_hoshi_size = int(width / 5)
        ctrl.ins_hoshi_pos = (width - ctrl.ins_hoshi_size) / 2

        ctrl.ins_stone_size = int(width)
        ctrl.ins_stone_pos = int((width - ctrl.ins_stone_size) / 2)

        ctrl.ins_font_height = int(width * 0.8)
        ctrl.ins_font_bottom = int((ctrl.ins_font_height - width) / 2)

        ctrl.ins_small_height = ctrl.ins_hoshi_size * 2
        ctrl.ins_small_pos = (width - ctrl.ins_small_height) / 2

    def eventFilter(self, object_, event):
        type_ = event.type()

        if type_ == QEvent.Enter:
            if self.status == EMPTY:
                self._hover = True
                self.repaint()
            return True
        if type_ == QEvent.Leave:
            self._hover = False
            self.repaint()
            return True

        return False
