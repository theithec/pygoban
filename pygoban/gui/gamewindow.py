import os
from threading import Timer

from pygoban.controller import Controller
from pygoban.coords import gtp_coords
from pygoban.game import End
from pygoban.move import Move
from pygoban.status import BLACK, EMPTY, WHITE, Status
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from . import BASE_DIR, CenteredMixin, InputMode, rotate
from .board import GuiBoard
from .intersection import Intersection
from .player import GuiPlayer
from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller, CenteredMixin):
    def __init__(self, black, white, game):
        super().__init__(black=black, white=white, game=game)
        self.board = GuiBoard(self, game)
        self.sidebar = Sidebar(self)

        self.setWindowIcon(QIcon(f'{BASE_DIR}/gui/imgs/icon.png'))
        self.input_mode = InputMode.PLAY
        self._deco = None
        Timer(1, lambda: self.set_turn(self.game.currentcolor, None)).start()

    def set_turn(self, color, result):
        # print(self.game.board)
        if result and not result.extra:
            if self.game.cursor and self.game.cursor.parent:
                comments = self.sidebar.comments.toPlainText().split(os.linesep)
                self.game.cursor.parent.extras.comments = comments
        if self.game.cursor:
            self.sidebar.game_signal.emit(os.linesep.join(self.game.cursor.extras.comments))
        if result and not result.extra:
            inter = self.board.intersections[gtp_coords(result.x, result.y, self.game.boardsize)]
            inter.status = result.color
            bsz = self.game.boardsize
            for killed in result.killed:
                self.board.intersections[gtp_coords(*rotate(*killed, bsz), bsz)].status = EMPTY

        self.sidebar.timeupdate_signal.emit()
        self.update_board()
        super().set_turn(color, result)

    def update_board(self):

        if Intersection.current:
            Intersection.current.is_current = False
        curr = self.game.cursor
        if not curr.is_empty:
            self.board.intersections[curr.coord].is_current = True

        self.board.update_intersections(self.game.board)
        self.sidebar.update_controlls()
        self.update()

    def period_ended(self, player):
        self.sidebar.timeupdate_signal.emit()

    def player_lost_by_overtime(self, player):
        self.sidebar.timeended_signal.emit()
        super().player_lost_by_overtime(player)

    def inter_clicked(self, inter: Intersection):
        if self.input_mode == InputMode.PLAY:
            if not self.game.currentcolor or not isinstance(
                    self.players[self.game.currentcolor], GuiPlayer):
                return
            self.handle_move(self.game.currentcolor, inter.coord)
        else:
            if self._deco in (BLACK, WHITE):
                move = (
                    self.game.cursor
                    if self.game.cursor.extras.stones
                    else Move(color=None, coord=None)
                )
                move.extras.stones[self._deco].add(inter.coord)
                self.game._test_move(move, apply_result=True)
                self.update_board()
            else:
                self.game.cursor.extras.decorations[inter.coord] = self.deco
                if self._deco == "NR":
                    self.game.cursor.extras.nr += 1
                elif self._deco == "CHAR":
                    self.game.cursor.extras.char = chr(ord(self.game.cursor.extras.char) + 1)

    def end(self, reason: End, color: Status):
        self.sidebar.timeended_signal.emit()
        super().end(reason, color)

    def resizeEvent(self, event):
        '''Overriden'''
        size = event.size()
        height = size.height()
        cmin = self.sidebar.minimumWidth()
        bwidth = size.width() - cmin
        mindim = min(height, bwidth)
        sizeborder = self.board.boardsize + 2
        mindim = int(mindim / sizeborder) * sizeborder
        self.sidebar.setGeometry(mindim, 0, bwidth + cmin - mindim, height)
        self.board.resize(mindim, mindim)
        self.center()

    @property
    def deco(self):
        if self._deco == "NR":
            return str(self.game.cursor.extras.nr)
        if self._deco == "CHAR":
            return self.game.cursor.extras.char
        return self._deco

    @deco.setter
    def deco(self, val):
        self._deco = val
