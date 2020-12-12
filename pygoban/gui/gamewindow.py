# pylint: disable=invalid-name
# because qt
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from pygoban.controller import Controller
from pygoban.game import MoveResult
from pygoban.move import Move
from pygoban.status import BLACK, EMPTY, WHITE, Status
from pygoban.rulesets import OccupiedViolation
from pygoban import InputMode, events

from . import BASE_DIR, CenteredMixin
from .guiboard import GuiBoard
from .intersection import Intersection
from .player import GuiPlayer
from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller, CenteredMixin):

    gameended_signal = pyqtSignal(str)

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
        self._deco = None
        self.gameended_signal.connect(self.gameended_action)

    def update_board(self, result: [events.Event], board):
        if isinstance(result, events.CursorChanged):
            if result.next_player and not self.timeout:
                for color in (BLACK, WHITE):
                    self.sidebar.controls[color].timeupdate_signal.emit()
        elif isinstance(result, events.Counted):
            # self.end(result.msg, color)
            if self.input_mode == InputMode.PLAY:
                self.input_mode = InputMode.COUNT
            # if self.input_mode == InputMode.ENDED:
            # btotal = result.points[BLACK] + result.prisoners[BLACK]
            # wtotal = result.points[WHITE] + result.prisoners[WHITE]
            # color = BLACK if btotal > wtotal else WHITE
        elif isinstance(result, events.Ended):
            self.mode = "EDIT"
            self.input_mode = InputMode.EDIT
            self.end(result.msg, result.color)
        self.sidebar.game_signal.emit(result)
        if board:
            self.guiboard.boardupdate_signal.emit(result, board)

        self.update()

    def update_moves(self, move: Move):
        print("update movesSET CURSOR")
        self.sidebar.editbox.tree.moves_signal.emit(move)
        self.guiboard.repaint()

    def period_ended(self, player):
        if not self.timeout:
            self.sidebar.controls[player.color].timeupdate_signal.emit()

    def inter_clicked(self, inter: Intersection):
        if self.input_mode == InputMode.PLAY:
            if not isinstance(
                self.players[self.last_move_result.next_player], GuiPlayer
            ):
                return
            try:
                self.callbacks["play"](self.last_move_result.next_player, inter.coord)
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
            # status = inter.status.toggle_dead()
            # for x, y in group:
            #    self.game.board[x][y] = status
            # self.count()

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
        self.sidebar.setGeometry(mindim, 0, bwidth + cmin - mindim, height)
        self.guiboard.resize(mindim, mindim)
        self.center()

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
