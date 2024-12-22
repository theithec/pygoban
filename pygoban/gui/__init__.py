import os
import signal
from enum import Enum
from typing import Callable, Protocol
from pygoban import results
from dataclasses import dataclass
from PyQt5 import QtWidgets

# kill with strg c
signal.signal(signal.SIGINT, signal.SIG_DFL)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GUIMode(Enum):
    EDIT = "EDIT"
    PLAY = "PLAY"
    COUNT = "COUNT"


@dataclass
class InsParams:
    """Values for all intersectionwidgets"""

    size: int = 0
    small_size: int = 0
    small_pos: int = 0
    hoshi_size: int = 0
    hoshi_pos: int = 0
    stone_size: int = 0
    stone_pos: int = 0
    font_height: int = 0
    font_bottom: int = 0
    small_font_height: int = 0
    small_font_bottom: int = 0
    small_bottom: int = 0


class GameUI(Protocol):
    gui_mode: GUIMode
    last_turn: results.TurnDone
    show_analyzed_variation: bool

    def foo(self, x, y): ...


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
