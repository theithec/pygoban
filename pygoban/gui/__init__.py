import os
import signal
from enum import Enum
from typing import Callable

from PyQt5 import QtWidgets

# kill with strg c
signal.signal(signal.SIGINT, signal.SIG_DFL)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GUIMode(Enum):
    EDIT = "EDIT"
    PLAY = "PLAY"
    COUNT = "COUNT"


class CenteredMixin:
    def center(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


def btn_adder(layout: QtWidgets.QLayout):
    def add_button(label: str, callback: Callable):
        button = QtWidgets.QPushButton(label)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    return add_button
