# pylint: disable=invalid-name
# because qt
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtMultimedia import QSound

from pygoban.controller import Controller
from pygoban.move import Move
from pygoban.status import BLACK, EMPTY, WHITE, Status, get_othercolor
from pygoban.rulesets import OccupiedViolation
from pygoban import InputMode
from pygoban.events import Event, CursorChanged, Counted, Ended

from . import BASE_DIR, CenteredMixin
from .guiboard import GuiBoard
from .intersection import Intersection
from .player import GuiPlayer
from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller, CenteredMixin):

    gameended_signal = pyqtSignal(str)
    movesound = QSound(os.path.join(BASE_DIR, "gui/sounds/stone.wav"))

    def __init__(self, black, white, callbacks, infos, mode, timesettings=None):
        super().__init__(
            black=black,
            white=white,
            callbacks=callbacks,
            infos=infos,
            mode=mode,
            timesettings=timesettings,
        )
        self.guiboard = GuiBoard(self, int(infos["SZ"]))
        self.sidebar = Sidebar(self)

        self.setWindowIcon(QIcon(f"{BASE_DIR}/gui/imgs/icon.png"))
        self.setWindowTitle(self.infos["GN"])
        self._deco = None
        self.gameended_signal.connect(self.gameended_action)

    def update_board(self, event: Event, board):
        if isinstance(event, CursorChanged):
            if event.next_player and not self.timeout:
                for color in (BLACK, WHITE):
                    self.sidebar.controls[color].timeupdate_signal.emit()
            if (
                self.mode == "PLAY"
                and self.input_mode == InputMode.PLAY
                and not event.cursor.is_empty
            ):
                self.movesound.play()

        elif isinstance(event, Counted):
            self.input_mode = InputMode.COUNT
        elif isinstance(event, Ended):
            self.mode = "EDIT"
            self.input_mode = InputMode.PLAY
            self.end(event.msg, event.color)

        self.sidebar.game_signal.emit(event)
        if board:
            self.guiboard.boardupdate_signal.emit(event, board)

        self.update()

    def update_moves(self, move: Move):
        self.sidebar.editbox.tree.moves_signal.emit(move)
        self.guiboard.repaint()

    def period_ended(self, player):
        if not self.timeout:
            self.sidebar.controls[player.color].timeupdate_signal.emit()

    def inter_rightclicked(self, inter: Intersection):
        cursor = self.last_move_result.cursor
        cursor.extras.decorations.pop(inter.coord, None)
        for color in (BLACK, WHITE):
            cursor.extras.stones[color].discard(inter.coord)
        cursor.extras.empty.discard(inter.coord)
        self.game_callback("set_cursor", self.last_move_result.cursor)

    def inter_leftclicked(self, inter: Intersection):
        if self.input_mode == InputMode.PLAY:
            color = self.last_move_result.next_player
            if not color:
                color = get_othercolor(self.last_move_result.cursor.color)
            if color and not isinstance(self.players[color], GuiPlayer):
                return
            try:
                self.callbacks["play"](color, inter.coord)
            except OccupiedViolation as err:
                print(err)
        elif self.input_mode == InputMode.EDIT:
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
        for color_ in (BLACK, WHITE):
            self.sidebar.controls[color_].timeended_signal.emit()
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

    def closeEvent(self, event):
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
