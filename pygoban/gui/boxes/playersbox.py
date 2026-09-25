# pylint: disable=abstract-method
# because qt and Box overloading
from typing import cast

from PyQt6.QtCore import Qt, QTimer, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QVBoxLayout,
)

from pygoban import Color, Party, results

from .. import GUIMode
from . import Box
from .playerbox import player_box_theme


def seconds_to_str(seconds):
    seconds = int(seconds)
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
        self.setTitle("")
        self.setObjectName("playerBox")
        self.player = player
        self.setStyleSheet(player_box_theme(player.color))

        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(18, 16, 18, 16)
        self.card_layout.setSpacing(10)

        header = QHBoxLayout()
        self.stone_label = QLabel()
        self.stone_label.setObjectName("stone")
        self.stone_label.setFixedSize(38, 38)
        self.stone_label.setStyleSheet(
            "background-color: #080808;"
            if player.color == Color.BLACK
            else "background-color: #ffffff;"
        )
        self.player_name_label = QLabel(player.name)
        self.player_name_label.setObjectName("playerName")
        header.addWidget(self.stone_label)
        header.addWidget(self.player_name_label)
        header.addStretch()
        self.card_layout.addLayout(header)

    def add_score_row(self, caption: str, value_label: QLabel) -> None:
        row = QHBoxLayout()
        caption_label = QLabel(caption)
        caption_label.setObjectName("prisonersTitle")
        row.addWidget(caption_label)
        row.addStretch()
        row.addWidget(value_label)
        if hasattr(self, "total_label") and value_label is not self.total_label:
            self.card_layout.insertLayout(self.card_layout.count() - 1, row)
        else:
            self.card_layout.addLayout(row)

    def received_turn(self, result: results.TurnDone):
        numdead = result.total_dead[self.player.color.other()]
        self.prisoners_label.setText(str(numdead))


class PlayerGameBox(_PlayerBox):
    timer = None
    _seconds: int
    clock_stop_signal = pyqtSignal()
    clock_update_signal = pyqtSignal(float, bool)

    def init(self, player: Party, **_kwargs) -> None:  # type: ignore
        super().init(player)
        self.clock = QLCDNumber()
        self.clock.setObjectName("clock")
        self.clock.setDigitCount(8)
        self.clock.setMinimumHeight(54)
        self.byoyomi_label = QLabel("")
        self.byoyomi_label.setObjectName("byoyomi")
        self.byoyomi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if time := self.game_ui.controller.ruleset.timesettings:
            self.set_byoyomi_text(
                periods_left=time.byoyomi_num, stones_left=time.byoyomi_stones
            )
            self.clock.display(seconds_to_str(0))
            self.card_layout.addWidget(self.clock)
            self.card_layout.addWidget(self.byoyomi_label)

        self.prisoners_label = QLabel(str(0))
        self.prisoners_label.setObjectName("prisoners")
        self.add_score_row("GEFANGENE STEINE", self.prisoners_label)
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
        # raise ValueError()
        if not (time := self.game_ui.controller.ruleset.timesettings):
            return
        txt = ""
        if time.byoyomi_num > 1:
            txt = f"{periods_left}/{time.byoyomi_num} periods"
        if time.byoyomi_stones > 1:
            if txt:
                txt += ", "
            txt += f"{time.byoyomi_stones - stones_left}/{time.byoyomi_stones} stones"

        self.byoyomi_label.setText(txt)

    def received_period_ended(self, result: results.TimeDone):
        if self.player.color != result.color:
            return
        b = result.byoyomi
        self.set_byoyomi_text(periods_left=b.periods_left, stones_left=b.stones_left)

        timesettings = self.game_ui.controller.ruleset.timesettings
        self.clock_update_signal.emit(
            result.next_time, timesettings and timesettings.use_clock
        )

    def received_turn(self, result: results.TurnDone):
        super().received_turn(result=result)
        if not (timesettings := self.game_ui.controller.ruleset.timesettings):
            return
        start_clock = timesettings.use_clock and self.game_ui.gui_mode == GUIMode.PLAY
        if result.next_color == self.player.color:
            if timesettings.use_clock:
                time_left = (
                    result.node.parent.annos.time_left
                    if result.node.parent
                    else timesettings.maintime
                )
                self.clock_update_signal.emit(time_left, start_clock)
        elif result.next_color.other() == self.player.color:
            if timesettings.use_clock:
                self.clock_stop_signal.emit()
            self.clock_update_signal.emit(result.node.annos.time_left, False)

            annos = result.node.annos
            self.set_byoyomi_text(annos.periods_left, annos.stones_left)


class PlayerCountBox(_PlayerBox):
    def init(self, player: Party):  # type: ignore  # pylint: disable=arguments-differ
        super().init(player)
        self.labels: dict[str, QLabel] = {}

        self.total_label = QLabel(str(0))
        self.total_label.setObjectName("totalLabel")
        self.add_score_row("GESAMTPUNKTE", self.total_label)


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
        self.last_gui_mode: GUIMode = self.game_ui.gui_mode
        for box in self.boxes_by_mode[self.game_ui.gui_mode].values():
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
        boxes = self.boxes_by_mode[GUIMode.COUNT]
        for color in (Color.BLACK, Color.WHITE):
            box = cast(PlayerCountBox, boxes[color])
            for caption, value in result[color].summands():
                if caption in box.labels:
                    box.labels[caption].setText(str(value))
                else:
                    box.labels[caption] = QLabel(str(value))
                    box.add_score_row(caption, box.labels[caption])

            total = result[color].total
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
