import os
from threading import Timer

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

from pygoban.controller import Controller
from pygoban.coords import gtp_coords
from pygoban.game import End
from pygoban.status import EMPTY, Status

from . import BASE_DIR, CenteredMixin, InputMode, rotate
from .board import GuiBoard
from .intersection import Intersection
from .player import GuiPlayer
from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller, CenteredMixin):
    def __init__(self, black, white, game, *args, **kwargs):
        super().__init__(black=black, white=white, game=game, *args, **kwargs)
        self.board = GuiBoard(self, game)
        self.sidebar = Sidebar(self)

        self.setWindowIcon(QIcon(f'{BASE_DIR}/gui/imgs/icon.png'))
        self.input_mode = InputMode.PLAY
        Timer(1, lambda: self.set_turn(self.game.currentcolor, None)).start()

    def set_turn(self, color, result):
        print(self.game._movetree.board)
        print(self.game._movetree.to_sgf())

        if result and not result.extra:
            if self.game.cursor and self.game.cursor.parent:
                comments = self.sidebar.comments.toPlainText().split(os.linesep)
                self.game.cursor.parent.comments = comments
        if self.game.cursor:
            self.sidebar.game_signal.emit(os.linesep.join(self.game.cursor.comments))
        if result and not result.extra:
            if Intersection.current:
                Intersection.current.is_current = False

            inter = self.board.intersections[gtp_coords(result.x, result.y, self.game.boardsize)]
            inter.status = result.color
            inter.is_current = True
            for killed in result.killed:
                self.board.intersections[gtp_coords(
                    *rotate(killed[0],killed[1], self.game.boardsize), self.game.boardsize)].status = EMPTY

        self.sidebar.timeupdate_signal.emit()
        self.sidebar.update_controlls()
        self.board.update_intersections(self.game._movetree.board)
        self.update()
        super().set_turn(color, result)

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
            self.game.cursor.decorations[inter.coord] = "A"

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
