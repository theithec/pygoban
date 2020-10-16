import os
from threading import Timer

from pygoban.controller import Controller
from pygoban.coords import letter_coord_from_int
from pygoban.game import End, Game
from pygoban.status import BLACK, EMPTY, Status
from PyQt5.QtGui import QColor, QImage, QPainter, QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from . import BASE_DIR, CenteredMixin
from .board import GuiBoard
from .player import GuiPlayer
from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller, CenteredMixin):
    def __init__(self, black, white, game, *args, **kwargs):
        super().__init__(black=black, white=white, game=game, *args, **kwargs)
        self.board = GuiBoard(self, game)
        self.sidebar = Sidebar(self)

        self.setWindowIcon(QIcon('gui/imgs/icon.png'))
        # self.setStyleSheet("background-color:black;")
        Timer(1, lambda: self.set_turn(self.game.currentcolor, None)).start()

    def set_turn(self, color, result):
        print(self.game.movetree.board)
        print(self.game.movetree.to_sgf())
        if result and not result.extra:
            for row in self.board.intersections:
                for inter in row:
                    if inter.is_current:
                        inter.is_current = False
                        break

            inter = self.board.intersections[result.y][result.x]
            inter.status = result.color
            inter.is_current = True
            for killed in result.killed:
                self.board.intersections[killed[1]][killed[0]].status = EMPTY

        self.sidebar.timeupdate_signal.emit()
        self.sidebar.update_controlls()
        super().set_turn(color, result)

    def period_ended(self, player):
        self.sidebar.timeupdate_signal.emit()

    def player_lost_by_overtime(self, player):
        self.sidebar.timeended_signal.emit()
        super().player_lost_by_overtime(player)

    def inter_clicked(self, inter):
        if not self.game.currentcolor or not isinstance(self.players[self.game.currentcolor], GuiPlayer):
            return
        x = letter_coord_from_int(inter.y, self.board.boardsize)
        y = self.board.boardsize - inter.x
        self.handle_move(self.game.currentcolor, f"{x}{y}")

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
