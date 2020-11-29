# pylint: disable=invalid-name
# because qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from pygoban.controller import Controller
from pygoban.game import End, MoveResult
from pygoban.move import Move
from pygoban.status import BLACK, EMPTY, WHITE, Status
from pygoban.rulesets import OccupiedViolation

from . import BASE_DIR, CenteredMixin, InputMode
from .guiboard import GuiBoard
from .intersection import Intersection
from .player import GuiPlayer
from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller, CenteredMixin):
    def __init__(self, black, white, callbacks, infos, timesettings=None):
        super().__init__(
            black=black,
            white=white,
            callbacks=callbacks,
            infos=infos,
            timesettings=timesettings,
        )
        self.guiboard = GuiBoard(self, infos["SZ"])
        self.sidebar = Sidebar(self)

        self.setWindowIcon(QIcon(f"{BASE_DIR}/gui/imgs/icon.png"))
        self.input_mode = InputMode.PLAY
        self._deco = None
        self.current_in = None  # "Active" intersection

    def update_board(self, result: MoveResult, board):
        move = result.move
        if self.current_in:
            self.current_in.is_current = False
        if not move.is_empty:
            self.guiboard.intersections[move.pos].is_current = True

        self.sidebar.timeupdate_signal.emit()
        self.guiboard.boardupdate_signal.emit(board)
        self.sidebar.game_signal.emit(result)
        self.update()

    def update_moves(self, move: Move):
        print("UPDATE MOVES1")
        self.sidebar.moves_signal.emit(move)

    def period_ended(self, player):
        self.sidebar.timeupdate_signal.emit()

    def player_lost_by_overtime(self, player):
        self.sidebar.timeended_signal.emit()
        super().player_lost_by_overtime(player)

    def inter_clicked(self, inter: Intersection):
        if self.input_mode == InputMode.PLAY:
            if not isinstance(self.players[self.last_result.next_player], GuiPlayer):
                return
            try:
                self.callbacks["play"](self.last_result.next_player, inter.coord)
            except OccupiedViolation as err:
                print(err)
        elif self.input_mode == InputMode.EDIT:
            if self._deco in (BLACK, WHITE):
                move = (
                    self.game.cursor if self.game.cursor.extras.has_stones() else Move()
                )
                move.extras.stones[self._deco].add(inter.coord)
                self.game._test_move(move, apply_result=True)
            else:
                self.last_result.move.extras.decorations[inter.coord] = self.deco
                if self._deco == "NR":
                    self.last_result.move.extras.nr += 1
                elif self._deco == "CHAR":
                    self.last_result.move.extras.char = chr(
                        ord(self.last_result.move.extras.char) + 1
                    )
        elif self.input_mode == InputMode.COUNT and inter.status != EMPTY:
            x, y = inter.coord
            group = self.callbacks["analyze"]((x, y), findkilled=False)[1]
            status = inter.status.toggle_dead()
            for x, y in group:
                self.game.board[x][y] = status
            self.count()

    def end(self, reason: End, color: Status):
        self.sidebar.timeended_signal.emit()
        super().end(reason, color)

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
        print("DD", self)
        if self._deco == "NR":
            return str(self.last_result.move.extras.nr)
        if self._deco == "CHAR":
            return self.last_result.move.extras.char
        return self._deco

    @deco.setter
    def deco(self, val):
        self._deco = val
