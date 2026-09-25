import logging
import os
import signal
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QLayout,
    QMainWindow,
    QPushButton,
    QWidget,
)

from pygoban import (
    MainGameController,
    Node,
    Parties,
    Settings,
    get_argparser,
    results,
)
from pygoban.rulesets import BaseRuleset as Ruleset
from pygoban.sgf import reader

# kill with ctrl+c
signal.signal(signal.SIGINT, signal.SIG_DFL)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GUIMode(Enum):
    EDIT = "EDIT"
    PLAY = "PLAY"
    COUNT = "COUNT"


@dataclass
class InsParams:
    """Shared values for all 'Intersection' widgets"""

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


def get_qsettings() -> QSettings:
    def ensure(groupname: str, data: dict):
        qsettings.beginGroup(groupname)
        for key, val in data.items():
            if (qval := qsettings.value(key)) is None:
                logging.debug(
                    "No value for '%s/%s' in qsettings. Use default '%s'",
                    groupname,
                    key,
                    val,
                )
                qsettings.setValue(key, val)
            else:
                logging.debug(
                    "Value for '%s/%s' from  qsettings: '%s'", groupname, key, qval
                )
        qsettings.endGroup()

    qsettings = QSettings("theithec", "pygoban")
    defaults = Settings()
    ensure(
        "board",
        {
            "size": defaults.boardsize,
            "komi": defaults.komi,
            "handicap": defaults.handicap,
        },
    )
    ensure(
        "clock",
        {
            "main_time": defaults.main_time,
            "byoyomi_time": defaults.byoyomi_time,
            "byoyomi_num": defaults.byoyomi_num,
            "byoyomi_stones": defaults.byoyomi_stones,
        },
    )
    ensure("players", {"black_name": "Black", "white_name": "White"})
    ensure("gtp", {"engines": {}})
    return qsettings


def merged_config() -> Settings:
    qsettings = get_qsettings()
    parser = get_argparser()
    argsdict = vars(parser.parse_args())
    if argsdict["time"]:
        parts = argsdict["time"].strip().split(":")
        timedict = dict(
            zip(("main_time", "byoyomi_time", "byoyomi_num", "byoyomi_stones"), parts)
        )
        argsdict.update(timedict)
    else:
        for key in ("main_time", "byoyomi_time", "byoyomi_num", "byoyomi_stones"):
            argsdict[key] = qsettings.value(f"clock/{key}")
    for vals in (
        ("black_name", "players/black_name"),
        ("white_name", "players/white_name"),
        ("boardsize", "board/size", int),
        ("komi", "board/komi", float),
        ("handicap", "board/handicap", int),
    ):
        akey, qkey = vals[0:2]
        func = vals[2] if len(vals) == 3 else str
        argsdict[akey] = func(argsdict[akey] or qsettings.value(qkey))

    argsdict["gtp_engines"] = qsettings.value("gtp/engines")
    argsdict.pop("time")
    return Settings(**argsdict)


class MainUI(QMainWindow):
    settings: Settings

    def add_game(
        self, mode: GUIMode, ruleset: Ruleset, cursor: Node | None = None
    ) -> MainGameController:
        raise NotImplementedError()

    def add_game_from_atomic_values(
        self,
        *,
        boardsize: int,
        komi: float,
        handicap: int,
        black_name: str,
        white_name: str,
        modestr: str,
        timestr: str,
        ruleset_name: str,
    ) -> MainGameController:
        raise NotImplementedError()

    def show_add_game_dialog(self):
        raise NotImplementedError()

    def show_edit_board_dialog(self):
        raise NotImplementedError()

    def load_sgf(self, path: str):
        ruleset, cursor = reader.load(path)
        self.add_game(mode=GUIMode.EDIT, ruleset=ruleset, cursor=cursor)


class ModeChangeListenerMixin:
    def mode_changed(self, gui_mode: GUIMode):
        pass


class GameUI(QWidget):
    main_ui: MainUI
    gui_mode: GUIMode
    initial_gui_mode: GUIMode
    show_analyzed_variation: bool
    controller: MainGameController
    parties: Parties
    last_turn: results.TurnDone | None = None
    annotation_type: str = ""
    mode_change_listeners: list[ModeChangeListenerMixin]

    def undo(self):
        raise NotImplementedError()

    def open_as_new(self):
        raise NotImplementedError()

    def inter_clicked(self, intersection, is_rightclick: bool):
        raise NotImplementedError()


class CenteredMixin:
    def center(self):
        qt_rectangle = self.frameGeometry()
        center_point = self.screen().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())


def btn_adder(layout: QLayout):
    def add_button(label: str, callback: Callable):
        button = QPushButton(label)
        button.clicked.connect(callback)
        layout.addWidget(button)
        return button

    return add_button
