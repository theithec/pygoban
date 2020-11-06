from typing import Callable
import enum
import os
from PyQt5 import QtWidgets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CenteredMixin:
    def center(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


class InputMode(enum.Enum):
    PLAY = "PLAY"
    EDIT = "EDIT"
    COUNT = "COUNT"


def rotate(x, y, boardsize):
    return (y, x)


def btn_adder(layout: QtWidgets.QLayout):
    def add_button(label: str, callback: Callable):
        button = QtWidgets.QPushButton(label)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    return add_button
