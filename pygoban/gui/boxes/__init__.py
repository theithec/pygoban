# pylint: disable=invalid-name, arguments-differ, abstract-method
# because qt and do_-commands and Box overloading
from copy import copy
from typing import Any, Callable, Type, TypeVar, Union, cast

from PyQt6.QtCore import Qt, QTimer, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtGui import QAction  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QGroupBox,
    QHBoxLayout,
    QLayout,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTextEdit,
    QWidget,
)

from pygoban import BaseReceiver, Color, Node, Party, gtp, results

from .. import GameUI, GUIMode, ModeChangeListenerMixin

# from .chart import MyChart


def _(txt):
    return txt


def btn_adder(
    layout: QLayout, buttoncls: Type[QPushButton] | Type[QRadioButton] = QPushButton
) -> Callable:
    def add_button(label: str, callback: Callable | None = None) -> QPushButton | QRadioButton:
        button = buttoncls(label)
        # m = QSizePolicy.Policy.Minimum
        button.setMinimumWidth(5)
        # button.setSizePolicy(m, m)
        if callback:
            button.clicked.connect(callback)  # type: ignore
        layout.addWidget(button)
        return button

    return add_button


class Box(QGroupBox, BaseReceiver, ModeChangeListenerMixin):
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
        self.game_ui.mode_change_listeners.append(self)
        self.kwargs = kwargs
        self.init(**kwargs)
        if self.events:
            self.game_ui.controller.add_receiver(self)

    def init(self, **kwargs):
        raise NotImplementedError()


BoxesByName = dict[str, Box]


class CommentsBox(Box):
    name = "CommentsBox"
    curr_node: results.TurnDone | None
    set_comment_signal = pyqtSignal(str)

    def init(self) -> None:  # type: ignore
        layout = QHBoxLayout()
        self.comments = QTextEdit()
        layout.addWidget(self.comments)
        self.set_comment_signal.connect(self.comments.setText)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setLayout(layout)
        self.events = {results.TurnDone}
        self.curr_node: results.TurnDone | None = None

    def received_turn(self, result):
        if self.curr_node:
            self.curr_node.annos.comment = self.comments.toPlainText().strip()
        # self.comments.setText(result.node.annos.comment)
        self.set_comment_signal.emit(result.node.annos.comment)
        self.curr_node = result.node
