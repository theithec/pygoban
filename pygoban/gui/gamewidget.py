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
    BaseReceiver,
    Color,
    Game,
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

# if TYPE_CHECKING:
#    from .mainwindow import MainWindow


class GameWidget(QWidget, BaseReceiver):
    gameended_signal = pyqtSignal(str)

    def __init__(
        self,
        parties: Parties,
        gui_mode: GUIMode,
        parent,  # "MainWindow",
        controller: GameController,
        # gtp_conns: dict,
    ) -> None:
        super().__init__(  # pylint: disable=unexpected-keyword-arg
            parent=parent,  # type:ignore
        )
        self.parties = parties
        self.controller = controller
        self._deco = None
        self.curr_action_result: ActionResult | None = None
        self.stonesound = QSound(os.path.join(BASE_DIR, "gui/sounds/stone.wav"))
        self.gui_mode = gui_mode
        self._initial_gui_mode = gui_mode
        self.callbacks = controller.callbacks
        self.boardwidget = BoardWidget(self, controller.ruleset.boardsize)
        self.bar = BarWidget(self)
        self.ruleset = controller.ruleset
        self.bar.btn_settings.setFocus()

    # def gameended_action(self, reason: str):
    #    msg = QMessageBox(self)
    #    msg.setIcon(QMessageBox.Information)
    #    msg.setText(reason)
    #    msg.show()

    def received_stone(self, result: ActionResult) -> None:
        # self.update()
        self.boardwidget.update()
        self.bar.result_signal.emit(result)

    def received_reset(self, result: ActionResult) -> None:
        self.boardwidget.update()

    def received_resign(self, result: ActionResult) -> None:
        pass

    def received_annotated(self, result: ActionResult) -> None:
        pass

    def received_count(self, result: ActionResult) -> None:
        pass

    def received_count_done(self, result: ActionResult) -> None:
        pass

    def received_period_ended(self, result: ActionResult) -> None:
        assert result.time_result
        color = result.time_result.color
        next_time = result.time_result.next_time
        box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][color]
        box.clock_update_signal.emit(next_time)
        box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][color.other()]
        box.clock_stop_signal.emit(0)

    def inter_clicked(self, iwidget: IntersectionWidget, is_rightclick: bool):
        assert self.controller.receiver.curr_action_result
        curr_action_result = self.controller.receiver.curr_action_result
        board = curr_action_result.board
        inter = board.intersection(iwidget.board_pos)
        # decobox = self.bar.inner.boxes["EditBox"].decobox
        # decogroup = self.bar.inner.boxes["EditBox"].decogroup
        iwidget._hover = False
        if is_rightclick:
            if (
                self.gui_mode == GUIMode.EDIT
                and self.bar.inner.boxes["EditBox"].decogroup.checkedButton()
            ):
                self.callbacks.annotate(iwidget.board_pos, Color.EMPTY)
        else:
            if self.gui_mode == GUIMode.COUNT:
                if inter.color:
                    self.callbacks.toggle_status(iwidget.board_pos)
            # elif self.gui_mode == GUIMode.EDIT and decobox.isChecked():
            #     if btn := decogroup.checkedButton():
            #         name = btn.text()
            #         print(btn, name)
            #         val: str | Marker | Color | None = None
            #         match name:
            #             case "B":
            #                 val = Color.BLACK
            #             case "W":
            #                 val = Color.WHITE
            #             case "TR":
            #                 val = Marker.TR
            #             case "SQ":
            #                 val = Marker.SQ
            #             case "CR":
            #                 val = Marker.CR
            #             case "1":
            #                 val = "1"
            #             case "A":
            #                 val = "A"
            #         print("V", val)
            #         if val:
            #             self.callbacks.annotate(pos=iwidget.board_pos, name=val)
            else:
                stone_result = self.controller.receiver.curr_stone_result
                # self.boardwidget.show_analyzed_variation = False
                if isinstance(self.parties[stone_result.next_color], GUIPlayer):
                    self.callbacks.play(
                        color=stone_result.next_color,
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

    def lost_by_overtime(self, color: Color):
        super().lost_by_overtime(color=color)
        for color in (Color.BLACK, Color.WHITE):
            box = self.bar.inner.playersbox.boxes_by_mode[self.gui_mode][color]
            box.clock_stop_signal.emit(0)

    def count_done(self):
        print("DONE")
        # self.gui_mode = GUIMode.EDIT
        # self.repaint()
        self.callbacks.finish()

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

        # self.bar.inner.setMinimumWidth(180)
        self.boardwidget.resize(mindim, mindim)
