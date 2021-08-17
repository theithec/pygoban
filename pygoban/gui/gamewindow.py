# pylint: disable=invalid-name
# because qt
import os
from enum import Enum
from typing import Dict

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from pygoban import InputMode
from pygoban.controller import ControllerMixin
from pygoban.events import Event, Counted, CursorChanged, Ended, Reset
from pygoban.player import Player
from pygoban.status import BLACK, EMPTY, WHITE, Status, get_othercolor
from pygoban.timesettings import TimeSettings

from . import BASE_DIR, CenteredMixin
from .guiboard import GuiBoard
from .intersection import Intersection
from .player import GuiPlayer
from .sidebar import Sidebar


class GuiMode(Enum):
    edit = "edit"
    play = "play"


class GameWindow(QMainWindow, ControllerMixin, CenteredMixin):

    gameended_signal = pyqtSignal(str)
    movesound = QSound(os.path.join(BASE_DIR, "gui/sounds/stone.wav"))

    def __init__(
        self,
        black: Player,
        white: Player,
        callbacks: Dict,
        infos: Dict,
        gui_mode: GuiMode = GuiMode.play,
        timesettings: TimeSettings = None,
        input_mode: InputMode = None,
    ):
        super().__init__(
            black=black,
            white=white,
            callbacks=callbacks,
            infos=infos,
            timesettings=timesettings,
            input_mode=input_mode,
        )
        self.gui_mode = gui_mode
        self.guiboard = GuiBoard(self, int(infos["SZ"]))
        self.sidebar = Sidebar(self)

        self.setWindowIcon(QIcon(f"{BASE_DIR}/gui/imgs/icon.png"))
        self.setWindowTitle(self.infos["GN"])
        self._deco = None
        self.gameended_signal.connect(self.gameended_action)

    def update_board(self, event: Event, board):

        if self.timesettings:
            for color in (BLACK, WHITE):
                clock = self.players[color].clock
                nexttime = clock.nexttime()  # type: ignore
                self.sidebar.controls[color].clock_stop_signal.emit(nexttime)
        if isinstance(event, CursorChanged):
            if event.reset == Reset.UNDO:
                self.update()
            if self.timesettings:
                if (color := event.cursor.color) in (BLACK, WHITE):  # type: ignore
                    self.sidebar.controls[color].clock_stop_signal.emit(
                        self.players[color].clock.nexttime()  # type: ignore
                    )
                self.sidebar.controls[event.next_player].clock_update_signal.emit(
                    self.players[event.next_player].clock.nexttime()  # type: ignore
                )
            if (
                self.gui_mode == GuiMode.play
                and self.input_mode == InputMode.PLAY
                and not event.cursor.is_empty
            ):
                self.movesound.play()
            self.sidebar.editbox.tree.moves_signal.emit(event.cursor)

        elif isinstance(event, Counted):
            self.input_mode = InputMode.COUNT
        elif isinstance(event, Ended):
            self.gui_mode = GuiMode.edit
            self.input_mode = InputMode.PLAY
            assert event.color
            self.end(event.msg, event.color)

        self.sidebar.game_signal.emit(event)
        if board:
            self.guiboard.boardupdate_signal.emit(event, board)
        self.update()

    def period_ended(self, player):
        super().period_ended(player)
        if not self.ended:
            self.sidebar.controls[player.color].clock_update_signal.emit(
                player.clock.nexttime()
            )

    def inter_rightclicked(self, inter: Intersection):
        assert self.last_move_result
        cursor = self.last_move_result.cursor
        cursor.extras.decorations.pop(inter.coord, None)
        for color in (BLACK, WHITE):
            cursor.extras.stones[color].discard(inter.coord)
        cursor.extras.empty.discard(inter.coord)
        self.game_callback("set_cursor", self.last_move_result.cursor)

    def inter_leftclicked(self, inter: Intersection):
        assert self.last_move_result
        print("S", self.input_mode)
        if self.input_mode == InputMode.PLAY:
            print("Si2", self.last_move_result)
            color = self.last_move_result.next_player
            if not color:
                color = get_othercolor(self.last_move_result.cursor.color)
            if not isinstance(self.players[color], GuiPlayer):
                return
            self._play(color, inter.coord)
        elif self.input_mode == InputMode.DECO:
            if self._deco in (BLACK, WHITE):
                self.last_move_result.cursor.extras.stones[self._deco].add(inter.coord)
            else:
                self.last_move_result.cursor.extras.decorations[inter.coord] = self.deco
                if self._deco == "NR":
                    self.last_move_result.cursor.extras.nr += 1
                elif self._deco == "CHAR":
                    self.last_move_result.cursor.extras.char = chr(
                        ord(self.last_move_result.cursor.extras.char) + 1
                    )
        elif self.input_mode == InputMode.COUNT and inter.status != EMPTY:
            x, y = inter.coord
            self.callbacks["toggle_status"]((x, y))  # , findkilled=False)[1]
        inter.repaint()

    def inter_clicked(self, inter: Intersection, is_rightclick):
        if is_rightclick:
            self.inter_rightclicked(inter)
        else:
            self.inter_leftclicked(inter)

    def gameended_action(self, reason: str):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText(reason)
        msg.show()

    def end(self, reason: str, color: Status):
        if self.timesettings:
            for color_ in (BLACK, WHITE):
                self.sidebar.controls[color_].clock_stop_signal.emit(
                    self.players[color_].clock.nexttime()  # type: ignore
                )
        super().end(reason, color)
        self.gameended_signal.emit(reason.format(color=color))

    def resizeEvent(self, event):
        size = event.size()
        height = size.height()
        cmin = self.sidebar.minimumWidth()
        bwidth = size.width() - cmin
        mindim = min(height, bwidth)
        sizeborder = self.guiboard.boardsize + 2
        mindim = int(mindim / sizeborder) * sizeborder
        width = bwidth + cmin - mindim
        left = mindim
        MAX_WIDTH = 360
        if width > MAX_WIDTH:
            left += (width - MAX_WIDTH) / 2
            width = MAX_WIDTH
        self.sidebar.setGeometry(left, 0, width, height)
        self.guiboard.resize(mindim, mindim)
        self.center()

    def closeEvent(self, _event):
        for player in self.players.values():
            player.end()

    @property
    def deco(self):
        if self._deco == "NR":
            return str(self.last_move_result.cursor.extras.nr)
        if self._deco == "CHAR":
            return self.last_move_result.cursor.extras.char
        return self._deco

    @deco.setter
    def deco(self, val):
        self._deco = val
