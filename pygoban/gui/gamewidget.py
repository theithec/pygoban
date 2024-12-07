# pylint: disable=invalid-name
# because qt
import os
from copy import copy
from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal  # pylint: disable=no-name-in-module
from PyQt5.QtMultimedia import QSound  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QMessageBox, QWidget  # pylint: disable=no-name-in-module

from pygoban import ActionType, TimeSettings

from .. import (  # ActionType,; GameResult,
    ActionResult,
    Color,
    GameController,
    Marker,
    Parties,
    Ruleset,
)
from . import BASE_DIR, GUIMode
from .barwidget import BarWidget
from .boardwidget import BoardWidget
from .intersections import IntersectionWidget
from .players import GUIPlayer

if TYPE_CHECKING:
    from .mainwindow import MainWindow


class GameWidget(QWidget, GameController):
    gameended_signal = pyqtSignal(str)

    def __init__(
        self,
        parent: "MainWindow",
        parties: Parties,
        ruleset: Ruleset,
        game_callbacks,
        gui_mode: GUIMode,
        timesettings: TimeSettings | None = None,
        # gtp_conns: dict,
    ) -> None:
        super().__init__(  # pylint: disable=unexpected-keyword-arg
            parent=parent,  # type:ignore
            parties=parties,  # type: ignore
            ruleset=ruleset,  # type: ignore
            game_callbacks=game_callbacks,  # type: ignore
            timesettings=timesettings,  # type: ignore
        )
        self.parties = parties
        self.controller = parent
        self._deco = None
        self.curr_action_result: ActionResult | None = None
        self.stonesound = QSound(os.path.join(BASE_DIR, "gui/sounds/stone.wav"))
        self.gui_mode = gui_mode
        self._initial_gui_mode = gui_mode
        self.boardwidget = BoardWidget(self, ruleset.boardsize)
        self.bar = BarWidget(self)
        self.ruleset = ruleset
        self.bar.btn_settings.setFocus()

    def receive_game_event(self, result: ActionResult):
        super().receive_game_event(result)
        # if isinstance(result, ActionResult):
        self.is_annotating = result.type == ActionType.ANNOTATED
        if result.type == ActionType.RESET:
            self.gui_mode = self._initial_gui_mode
        if result.stone_result:
            stone = result.stone_result.stone
            if stone.annos.time_left:
                last_color = (
                    stone.color
                    if stone.color != Color.EMPTY
                    else (
                        Color.BLACK
                        if result.stone_result.next_color == Color.WHITE
                        else Color.WHITE
                    )
                )  # last = last/current stone vs next stone

                if result.type in (ActionType.STONE, ActionType.RESET):
                    next_time = stone.annos.time_left.get(result.stone_result.next_color)
                    last_time = (
                        stone.annos.time_left[last_color]
                        if stone.color != Color.EMPTY
                        else next_time
                    )
                    last_box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][last_color]
                    next_box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][
                        result.stone_result.next_color
                    ]
                    if last_time:
                        last_box.clock_stop_signal.emit(last_time)
                    if next_time:
                        next_box.clock_update_signal.emit(next_time)
            # if result.type != ActionType.ANNOTATED:
            #    print("EMIT1")
            # self.bar.result_signal.emit(result)
        elif result.game_result:
            if result.type == ActionType.COUNT:
                self.gui_mode = GUIMode.COUNT
            # self.bar.result_signal.emit(result)
            # print("EMIT2")
        self.bar.result_signal.emit(result)
        self.boardwidget.boardupdate_signal.emit(result)

    # def gameended_action(self, reason: str):
    #    msg = QMessageBox(self)
    #    msg.setIcon(QMessageBox.Information)
    #    msg.setText(reason)
    #    msg.show()

    def inter_clicked(self, iwidget: IntersectionWidget, is_rightclick: bool):
        assert self.curr_action_result
        board = self.curr_action_result.board
        inter = board.intersection(iwidget.board_pos)
        decobox = self.bar.inner.boxes["EditBox"].decobox
        decogroup = self.bar.inner.boxes["EditBox"].decogroup
        iwidget._hover = False
        if is_rightclick:
            if (
                self.gui_mode == GUIMode.EDIT
                and self.bar.inner.boxes["EditBox"].decogroup.checkedButton()
            ):
                self.game_callbacks.annotate(iwidget.board_pos, Color.EMPTY)
        else:
            if self.gui_mode == GUIMode.COUNT:
                if inter.color:
                    self.game_callbacks.toggle_status(iwidget.board_pos)
            elif self.gui_mode == GUIMode.EDIT and decobox.isChecked():
                if btn := decogroup.checkedButton():
                    name = btn.text()
                    print(btn, name)
                    val: str | Marker | Color | None = None
                    match name:
                        case "B":
                            val = Color.BLACK
                        case "W":
                            val = Color.WHITE
                        case "TR":
                            val = Marker.TR
                        case "SQ":
                            val = Marker.SQ
                        case "CR":
                            val = Marker.CR
                        case "1":
                            val = "1"
                        case "A":
                            val = "A"
                    print("V", val)
                    if val:
                        self.game_callbacks.annotate(pos=iwidget.board_pos, name=val)

            else:
                assert self.curr_action_result.stone_result
                color = self.curr_action_result.stone_result.next_color
                assert color
                # self.boardwidget.show_analyzed_variation = False
                if isinstance(self.parties[color], GUIPlayer):
                    self.game_callbacks.play(
                        color=self.curr_action_result.stone_result.next_color,
                        pos=iwidget.board_pos,
                    )

    def open_as_new(self):
        ruleset = copy(self.ruleset)
        assert self.curr_action_result
        cpy = self.curr_action_result.stone.as_copy()
        self.controller._add_game(
            mode=GUIMode.EDIT.value,
            ruleset=ruleset,
            cursor=cpy,
        )

    def period_ended(self, color: Color):
        assert self.clocks
        box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][color]
        box.clock_update_signal.emit(self.clocks[color].nexttime())

    def lost_by_overtime(self, color: Color):
        super().lost_by_overtime(color=color)
        for color in (Color.BLACK, Color.WHITE):
            box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][color]
            box.clock_stop_signal.emit(0)

    def count_done(self):
        print("DONE")
        # self.gui_mode = GUIMode.EDIT
        # self.repaint()
        self.game_callbacks.finish()

    # @property
    # def deco(self):
    #    if self._deco == "NR":
    #        return str(self.last_stone_result.cursor.extras.nr)
    #    if self._deco == "CHAR":
    #        return self.last_stone_result.cursor.extras.char
    #    return self._deco

    # @deco.setter
    # def deco(self, val):
    #    self._deco = val
    def resizeEvent(self, event):
        size = event.size()
        height = size.height()
        bwidth = size.width()
        mindim = min(height, bwidth)
        sizeborder = self.boardwidget.boardsize + 2
        mindim = int(mindim / sizeborder) * sizeborder
        width = bwidth - mindim
        left = mindim + sizeborder
        MAX_WIDTH = 800
        if width > MAX_WIDTH:
            left += width - MAX_WIDTH  # / 2
            width = MAX_WIDTH  # - mindim
        self.bar.setGeometry(left, 0, width, height)

        self.bar.inner.setMinimumWidth(180)
        self.boardwidget.resize(mindim, mindim)
