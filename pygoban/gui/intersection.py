# pylint: disable=invalid-name, comparison-with-callable, using-constant-test
import os

from PyQt5.QtCore import QRect, Qt, pyqtProperty, QEvent
from PyQt5.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import QWidget  # pylint: disable=no-name-in-module

from pygoban.status import Status, STATUS,  BLACK, WHITE, DEAD_BLACK, DEAD_WHITE, EMPTY

from . import BASE_DIR


class Intersection(QWidget):
    """Visual representation of a intersection in a go board"""
    boardsize = 9
    stone_by_status = {
        BLACK: QImage(os.path.join(BASE_DIR, "gui/imgs/black.png")),
        WHITE: QImage(os.path.join(BASE_DIR, "gui/imgs/white.png")),
        DEAD_BLACK: QImage(os.path.join(BASE_DIR, "gui/imgs/black_trans.png")),
        DEAD_WHITE: QImage(os.path.join(BASE_DIR, "gui/imgs/white_trans.png")),
    }

    def __init__(self, parent, x, y, status, is_hoshi):
        super().__init__(parent)
        self.controller = parent.parent()
        self.x = x
        self.y = y
        self._status = status
        self._marker = ""
        self.is_hoshi = is_hoshi
        self._is_current = None
        self._hover = False
        self.installEventFilter(self)

    @pyqtProperty(bool)
    def is_current(self):
        return self._is_current

    @is_current.setter
    def is_current(self, _is_current):
        if self._is_current != _is_current:
            self._is_current = _is_current
            self.update()

    @pyqtProperty(int)
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if status != self._status:
            self._status = status
            self.update()

    @pyqtProperty(str)
    def marker(self):
        return self._marker

    @marker.setter
    def marker(self, marker):
        if marker != self._marker:
            self._marker = marker
            self.update()

    def mousePressEvent(self, event):
        """Clck"""
        self.controller.inter_clicked(self)

    def paintEvent(self, _):
        """Draw"""

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHints(
            painter.Antialiasing |
            painter.SmoothPixmapTransform |
            painter.HighQualityAntialiasing)
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor("black"))
        painter.setPen(pen)
        cls = self.__class__

        if self.is_hoshi:
            hosz = cls.curr_hoshi_size
            hosp = cls.curr_hoshi_pos
            painter.setBrush(QColor("black"))
            painter.drawEllipse(hosp, hosp, hosz, hosz)

        stone_img = self.stone_by_status.get(self.status)
        if self.controller.game.currentcolor and self._hover and not stone_img:
            stone_img = self.stone_by_status.get(
                STATUS[self.controller.game.currentcolor.intval + 2])

        if stone_img:
            pixmap = QPixmap(stone_img)
            painter.drawPixmap(
                QRect(
                    cls.curr_stone_pos,
                    cls.curr_stone_pos,
                    cls.curr_stone_size,
                    cls.curr_stone_size),
                pixmap)

        if self.marker:
            font = painter.font()
            font.setPixelSize(cls.curr_font_height / 2)
            painter.setFont(font)
            painter.setPen(QColor("green"))
            painter.drawText(
                QRect(0, cls.curr_font_bottom, cls.curr_width,
                      cls.curr_width),
                Qt.AlignCenter, self.marker)

        if self.is_current:
            painter.setBrush(QColor("red"))
            painter.drawEllipse(
                cls.curr_curr_pos,
                cls.curr_curr_pos,
                cls.curr_curr_height,
                cls.curr_curr_height,
            )

        painter.end()

    def calc(self):
        """Calc for one - use for all"""
        cls = self.__class__
        width = self.width()
        cls.curr_width = width

        cls.curr_hoshi_size = int(width / 5)
        cls.curr_hoshi_pos = (width - cls.curr_hoshi_size) / 2

        cls.curr_stone_size = int(width * 1)
        cls.curr_stone_pos = int((width - cls.curr_stone_size) / 2)

        cls.curr_font_height = int(width * .8)
        cls.curr_font_bottom = int((cls.curr_font_height - width) / 2)

        cls.curr_curr_height = cls.curr_hoshi_size * 2
        cls.curr_curr_pos = (width - cls.curr_curr_height) / 2

    def eventFilter(self, object_, event):
        type_ = event.type()

        if type_ == QEvent.Enter:
            if self.status == EMPTY:
                self._hover = True
                self.repaint()
            return True
        elif type_ == QEvent.Leave:
            self._hover = False
            self.repaint()
            return True

        return False
