# pylint: disable=invalid-name, arguments-differ
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

from pygoban import Color, Party, results, gtp

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


def seconds_to_str(seconds):
    hours = int(seconds / 360) if seconds >= 360 else 0
    seconds -= hours * 360
    minutes = int(seconds / 60) if seconds >= 60 else 0
    seconds -= minutes * 60
    txt = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return txt


class Box(QGroupBox):
    game_ui: GameUI
    name: str
    toggle_action: QAction

    def __init__(self, parent: QWidget, **kwargs):
        super().__init__(parent=parent, visible=kwargs.pop("visible", True))  # type: ignore
        curr: Any = parent
        while str(curr.__class__.__name__) != "GameWidget":
            curr = curr.parent()
        self.game_ui: GameUI = curr
        self.kwargs = kwargs
        self.init(**kwargs)

    def init(self, **kwargs):
        raise NotImplementedError()


BoxesByName = dict[str, Box]


class _PlayerBox(Box):
    name = "_Player"
    prisoners_label: QLabel
    byoyomi_label: QLabel
    clock: QLCDNumber

    def __init__(self, parent: "PlayersBox", **kwargs):
        super().__init__(parent, visible=False, **kwargs)

    def init(self, player: Party):  # type: ignore
        self.setTitle(player.name)
        self.player = player

        self.othercolor = Color.WHITE if player.color == Color.BLACK else Color.BLACK
        fg = "#eeeeee" if player.color == Color.BLACK else "#011111"
        bg = "#eeeeee" if player.color == Color.WHITE else "#011111"

        colors = f"""
           background-color : {bg};
           color: {fg} ;
        """
        clsname = self.__class__.__name__
        css1 = f"""
        {clsname} {{
           padding-top: 2ex; /* leave space at the top for the title */
           background-color: {bg};
           {colors}
        }}
        {clsname}::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left; /* position at the top center */
           {colors}
        }}
        QLabel{{
           {colors}
        }}
        QRow#total_row {{
           font-weight: bold;
        }}
        QLabel#total_label{{
           {colors}
           font-weight: bold;
        }}

        """
        self.setStyleSheet(css1)
        self.formlayout = QFormLayout()
        self.prisoners_label = QLabel(str(0))
        self.formlayout.addRow("Prisoners:", self.prisoners_label)


class PlayerGameBox(_PlayerBox):
    timer = None
    _seconds: int

    def clockdisplay_tick(self):
        self._seconds -= 1
        txt = seconds_to_str(self._seconds)
        self.clock.display(txt)

    def stop_clockdisplay(self, seconds: int | None = None):
        if self.timer:
            self.timer.stop()
        if seconds is not None:
            self.clock.display(seconds_to_str(seconds))

    def set_clockdisplay(self, seconds):
        # seconds = seconds or self._seconds
        self.stop_clockdisplay(seconds)
        self._seconds = seconds

        if seconds > 0:
            self.timer = QTimer(self)
            self.timer.start(1000)
            self.clock.display(seconds_to_str(seconds))
            self.timer.timeout.connect(self.clockdisplay_tick)
        else:
            self.clock.display("00:00")

    def init(self, player: Party, **_kwargs) -> None:  # type: ignore
        super().init(player)
        self.clock = QLCDNumber()
        self.byoyomi_label = QLabel("")
        self.clock.display(seconds_to_str(0))
        self.formlayout.addRow(self.clock)
        self.setLayout(self.formlayout)


class PlayerCountBox(_PlayerBox):
    def init(self, player: Party):  # type: ignore
        super().init(player)
        self.libs_label = QLabel(str(0))
        self.formlayout.addRow("Liberties:", self.libs_label)

        if player.color == Color.WHITE:
            self.formlayout.addRow("Komi:", QLabel(str(self.game_ui.controller.ruleset.komi)))
        else:
            self.formlayout.addRow("", QLabel(""))
        self.total_label = QLabel(str(0))
        self.total_label.setObjectName("total_label")
        self.formlayout.addRow("", self.total_label)
        self.setLayout(self.formlayout)


class PlayersBox(Box):
    name = "PlayerBox"
    last_gui_mode: GUIMode = GUIMode.PLAY

    def init(self, players: dict[Color, Party]):  # type: ignore
        self.boxlayout = QHBoxLayout()
        self.boxes_by_mode: dict[GUIMode, dict[Color, PlayerCountBox | PlayerGameBox]] = {
            GUIMode.PLAY: {
                Color.BLACK: PlayerGameBox(self, player=players[Color.BLACK]),
                Color.WHITE: PlayerGameBox(self, player=players[Color.WHITE]),
            },
            GUIMode.COUNT: {
                Color.BLACK: PlayerCountBox(self, player=players[Color.BLACK]),
                Color.WHITE: PlayerCountBox(self, player=players[Color.WHITE]),
            },
        }
        self.boxes_by_mode[GUIMode.EDIT] = self.boxes_by_mode[GUIMode.PLAY]
        for box in self.boxes_by_mode[self.game_ui.gui_mode].values():
            self.last_gui_mode: GUIMode = self.game_ui.gui_mode
            self.boxlayout.addWidget(box)
            box.setVisible(True)
        self.setLayout(self.boxlayout)

    def set_boxes(self):
        print("SET BOXES", self.last_gui_mode, self.game_ui.gui_mode)
        if self.last_gui_mode != self.game_ui.gui_mode:
            curr_boxes = self.boxes_by_mode[self.last_gui_mode]
            next_boxes = self.boxes_by_mode[self.game_ui.gui_mode]
            for color in (Color.BLACK, Color.WHITE):
                self.boxlayout.replaceWidget(
                    curr_boxes[color],
                    next_boxes[color],
                )
                curr_boxes[color].setVisible(False)
                next_boxes[color].setVisible(True)  # True)
        self.last_gui_mode = self.game_ui.gui_mode


class GameBox(Box):
    name = "GameBox"

    def init(self, **kwargs) -> None:
        layout = QHBoxLayout()
        controller = self.game_ui.controller
        self.action_mapping = {
            "Pass": self.game_ui.controller.do_pass,
            "Resign": lambda: controller.set_end_result(
                results.GameResultType.RESIGN,
                color=cast(results.TurnDone, self.game_ui.last_turn).next_color,
            ),
            "Undo": controller.undo,
            "Done": lambda: controller.set_end_result(results.GameResultType.COUNTED),
        }

        add_gamebutton = btn_adder(layout)
        self.buttons = {}

        for action, mapping in self.action_mapping.items():
            self.buttons[action] = add_gamebutton(action, mapping)

        self.setLayout(layout)

    def update_controlls(self, result: results.TurnDone):
        pass


class EditBox(Box):
    name = "EditBox"

    def init(self):
        box_layout = QFormLayout()
        btns_layout = QHBoxLayout()
        controller = self.game_ui.controller
        add_dirbutton = btn_adder(btns_layout)
        self.btn_first_stone = add_dirbutton("|<", controller.do_first_stone)
        self.btn_prev_var = add_dirbutton("<<", controller.do_prev_variation)
        self.btn_prev_stone = add_dirbutton("<", controller.do_prev_stone)
        self.btn_next_stone = add_dirbutton(">", controller.do_next_stone)
        self.btn_next_var = add_dirbutton(">>", controller.do_next_variation)
        self.btn_last_stone = add_dirbutton(">|", controller.do_last_stone)
        # self.btn_auto = add_dirbutton("auto", controller.toggle_auto)
        self.btn_auto = add_dirbutton("Pass", controller.do_pass)
        self.btn_auto.setCheckable(True)
        # self.btn_count = add_dirbutton("Count", self.toggle_count)
        # self.btn_count.setCheckable(True)

        deco_layout = QHBoxLayout()
        add_decobutton = btn_adder(deco_layout, QRadioButton)
        self.decobox = QGroupBox("Deco")
        self.decogroup = QButtonGroup()
        self.decobox.setCheckable(True)
        self.decobox.setChecked(False)
        self.decobox.toggled.connect(self.toggle_deco)
        self.decogroup.addButton(add_decobutton("B"))
        self.decogroup.addButton(add_decobutton("W"))
        self.decogroup.addButton(add_decobutton("TR"))
        self.decogroup.addButton(add_decobutton("SQ"))
        self.decogroup.addButton(add_decobutton("CR"))
        self.decogroup.addButton(add_decobutton("1"))
        self.decogroup.addButton(add_decobutton("A"))
        self.decobox.setLayout(deco_layout)

        box_layout.addRow(btns_layout)
        box_layout.addRow(self.decobox)
        self.setLayout(box_layout)

    def toggle_deco(self):
        self.game_ui.is_annotating = self.decobox.isChecked()

    def do_nr(self):
        pass

    def do_char(self):
        pass

    def update_controlls(self, result: results.TurnDone):
        stone = result.node
        has_parent = bool(stone.parent)
        has_children = bool(stone.children)
        self.btn_first_stone.setEnabled(has_parent)
        self.btn_prev_var.setEnabled(has_parent)
        self.btn_prev_stone.setEnabled(has_parent)
        self.btn_next_stone.setEnabled(has_children)
        self.btn_next_var.setEnabled(has_children)
        self.btn_last_stone.setEnabled(has_children)


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
