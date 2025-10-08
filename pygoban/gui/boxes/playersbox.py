# pylint: disable=abstract-method
# because qt and do_-commands and Box overloading
from typing import cast
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
)
from PyQt6.QtCore import QTimer, pyqtSignal  # pylint: disable=no-name-in-module

from pygoban import Color, Party, results
from .. import GUIMode

from . import Box


def seconds_to_str(seconds):
    hours = int(seconds / 360) if seconds >= 360 else 0
    seconds -= hours * 360
    minutes = int(seconds / 60) if seconds >= 60 else 0
    seconds -= minutes * 60
    txt = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return txt


class _PlayerBox(Box):
    name = "_Player"
    prisoners_label: QLabel
    byoyomi_label: QLabel
    clock: QLCDNumber

    def __init__(self, parent: "PlayersBox", **kwargs):
        super().__init__(parent, visible=False, **kwargs)

    def init(self, player: Party):  # type: ignore  # pylint: disable=arguments-differ
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

    def received_turn(self, result: results.TurnDone):
        numdead = result.total_dead[self.player.color.other()]
        self.prisoners_label.setText(str(numdead))


class PlayerGameBox(_PlayerBox):
    timer = None
    _seconds: int
    clock_stop_signal = pyqtSignal()
    clock_update_signal = pyqtSignal(int, bool)

    def init(self, player: Party, **_kwargs) -> None:  # type: ignore
        super().init(player)
        self.clock = QLCDNumber()
        self.byoyomi_label = QLabel("")
        if time := self.game_ui.controller.ruleset.timesettings:
            self.set_byoyomi_text(
                periods_left=time.byoyomi_num, stones_left=time.byoyomi_stones
            )
            self.clock.display(seconds_to_str(0))
            self.formlayout.addRow(self.clock)
            self.formlayout.addRow(self.byoyomi_label)
        self.setLayout(self.formlayout)
        self.clock_stop_signal.connect(self.stop_clock)
        self.clock_update_signal.connect(self.clock_update)
        self.events = {results.TurnDone, results.TimeDone}

    def stop_clock(self):
        if self.timer:
            self.timer.stop()
        # if seconds != -1:  # 'None' does  not work with signals
        #    self.clock.display(seconds_to_str(seconds))

    def clockdisplay_tick(self):
        self._seconds -= 1
        txt = seconds_to_str(self._seconds)
        self.clock.display(txt)

    def clock_update(self, seconds, start_timer=False):
        self._seconds = seconds
        if start_timer:
            self.stop_clock()
            self.timer = QTimer(self)
            self.timer.start(1000)
            self.timer.timeout.connect(self.clockdisplay_tick)
        self.clock.display(seconds_to_str(seconds))

    def set_byoyomi_text(self, periods_left, stones_left):
        if not (time := self.game_ui.controller.ruleset.timesettings):
            return
        txt = ""
        if time.byoyomi_num > 1:
            txt = f"{periods_left}/{time.byoyomi_num} periods"
        if time.byoyomi_stones > 1:
            if txt:
                txt += ", "
            txt += f"{stones_left}/{time.byoyomi_stones} stones"
        self.byoyomi_label.setText(txt)

    def received_period_ended(self, result: results.TimeDone):
        if self.player.color != result.color:
            return
        b = result.byoyomi
        self.set_byoyomi_text(periods_left=b.periods_left, stones_left=b.stones_left)
        self.clock_update_signal.emit(result.next_time, True)

    def received_turn(self, result: results.TurnDone):
        super().received_turn(result=result)
        if not (timesettings := self.game_ui.controller.ruleset.timesettings):
            return
        if result.next_color == self.player.color:
            time_left = (
                result.node.parent.annos.time_left
                if result.node.parent
                else timesettings.maintime
            )
            self.clock_update_signal.emit(time_left, True)
        elif result.next_color.other() == self.player.color:
            self.clock_stop_signal.emit()
            self.clock_update_signal.emit(result.node.annos.time_left, False)


class PlayerCountBox(_PlayerBox):
    def init(self, player: Party):  # type: ignore
        super().init(player)
        self.libs_label = QLabel(str(0))
        self.formlayout.addRow("Liberties:", self.libs_label)

        if player.color == Color.WHITE:
            self.formlayout.addRow(
                "Komi:", QLabel(str(self.game_ui.controller.ruleset.komi))
            )
        else:
            self.formlayout.addRow("", QLabel(""))
        self.total_label = QLabel(str(0))
        self.total_label.setObjectName("total_label")
        self.formlayout.addRow("", self.total_label)
        self.setLayout(self.formlayout)


class PlayersBox(Box):
    name = "PlayerBox"
    last_gui_mode: GUIMode = GUIMode.PLAY

    def init(self, players: dict[Color, Party]):  # type: ignore  # pylint: disable=arguments-differ
        self.boxlayout = QHBoxLayout()
        self.boxes_by_mode: dict[
            GUIMode, dict[Color, PlayerCountBox | PlayerGameBox]
        ] = {
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

        self.events = {results.GameResultDone, results.Counted}
        self.setLayout(self.boxlayout)

    def received_result_done(self, result: results.GameResultDone):
        if not self.game_ui.controller.ruleset.timesettings:
            return
        boxes = self.boxes_by_mode[GUIMode.PLAY]
        for box in boxes.values():
            cast(PlayerGameBox, box).clock_stop_signal.emit()

    def received_count(self, result: results.Counted):
        boxes = self.boxes_by_mode[self.game_ui.gui_mode]
        for color in (Color.BLACK, Color.WHITE):
            box = boxes[color]
            assert isinstance(box, PlayerCountBox), box
            box.clock_stop_signal.emit()
            playerresult = result[color]
            numcoords = len(playerresult.coords)
            box.libs_label.setText(str(numcoords))
            box.prisoners_label.setText(str(playerresult.killed))
            total = playerresult.total()
            if box.player.color == Color.WHITE:
                total += self.game_ui.controller.ruleset.komi
            box.total_label.setText(str(total))

    def mode_changed(self, gui_mode: GUIMode):
        if self.last_gui_mode != gui_mode:
            curr_boxes = self.boxes_by_mode[self.last_gui_mode]
            next_boxes = self.boxes_by_mode[gui_mode]
            for color in (Color.BLACK, Color.WHITE):
                self.boxlayout.replaceWidget(
                    curr_boxes[color],
                    next_boxes[color],
                )
                curr_boxes[color].setVisible(False)
                next_boxes[color].setVisible(True)
        self.last_gui_mode = gui_mode
