from threading import Timer
import os
from PyQt5.QtWidgets import (QMainWindow, QMessageBox)
from PyQt5.QtGui import QColor, QImage, QPainter
from lib.controller import Controller
from lib.coords import letter_coord_from_int
from .player import GuiPlayer
from . import BASE_DIR
from lib.status import BLACK, EMPTY
from .board import GuiBoard

from .sidebar import Sidebar


class GameWindow(QMainWindow, Controller):
    def __init__(self, black, white, game, *args, **kwargs):
        super().__init__(black=black, white=white, game=game, *args, **kwargs)
        self.board = GuiBoard(self, game)
        self.sidebar = Sidebar(self)
        # self.setStyleSheet("background-color:black;")
        Timer(1, lambda: self.set_turn(BLACK, None)).start()

    def set_turn(self, color, result):
        print(self.game.movetree.board)
        print(self.game.movetree.to_sgf())
        if result:
            if result.extra:
                return

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
        super().set_turn(color, result)

    def overtime_happend(self, player):
        self.sidebar.timeupdate_signal.emit()

    def player_lost_by_overtime(self, player):
        self.sidebar.timeended_signal.emit()
        super().player_lost_by_overtime(player)

    def inter_clicked(self, inter):
        if not isinstance(self.players[self.game.currentcolor], GuiPlayer):
            return
        x = letter_coord_from_int(inter.y, self.board.boardsize)
        y = self.board.boardsize - inter.x
        self.handle_move(self.game.currentcolor, f"{x}{y}")
        self.sidebar.update_controlls()

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
