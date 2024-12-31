# pylint: disable=invalid-name, arguments-differ, abstract-method
# because qt and do_-commands and Box overloading
from typing import Any, Callable, Type, TypeVar, cast, Union
from copy import copy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QButtonGroup,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLCDNumber,
    QMenu,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QWidget,
)
from PyQt6.QtGui import QAction  # pylint: disable=no-name-in-module

from pygoban import Color, Party, results, gtp, BaseReceiver

from .. import GUIMode, GameUI

# from .chart import MyChart


def _(txt):
    return txt


def btn_adder(
    layout: QLayout, buttoncls: Type[QPushButton] | Type[QRadioButton] = QPushButton
) -> Callable:
    def add_button(label: str, callback: Callable | None = None) -> QPushButton | QRadioButton:
        button = buttoncls(label)
        if callback:
            button.clicked.connect(callback)  # type: ignore
        layout.addWidget(button)
        return button

    return add_button


class Box(QGroupBox, BaseReceiver):
    game_ui: GameUI
    name: str
    toggle_action: QAction

    def __init__(self, parent: QWidget, **kwargs):
        super().__init__(  # type: ignore  # pylint: disable=unexpected-keyword-arg
            parent=parent, visible=kwargs.pop("visible", True)
        )
        curr: Any = parent
        while str(curr.__class__.__name__) != "GameWidget":
            curr = curr.parent()
        self.game_ui: GameUI = curr
        self.kwargs = kwargs
        self.init(**kwargs)
        if self.events:
            self.game_ui.controller.add_receiver(self)

    def init(self, **kwargs):
        raise NotImplementedError()


BoxesByName = dict[str, Box]


class CommentsBox(Box):
    name = "CommentsBox"

    def init(self):  # type: ignore
        layout = QHBoxLayout()
        self.comments = QTextEdit()
        layout.addWidget(self.comments)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setLayout(layout)

    def update_controlls(self, result: results.TurnDone):
        self.comments.setText(result.node.annos.comment)
