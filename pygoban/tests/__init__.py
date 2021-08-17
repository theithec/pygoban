import mock
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget
from pygoban.status import BLACK, WHITE
from pygoban.player import Player
from pygoban.events import CursorChanged
from pygoban.game import Game
from pygoban.controller import Controller
import pygoban.startgame
from pygoban import get_argparser
from PyQt5.QtWidgets import QApplication


pygoban.startgame.QAPP = QApplication([])


class MockedPlayer(Player):
    MOVES = ("a1", "a2", "a3")

    @classmethod
    def moves(cls):
        for move in cls.MOVES:
            yield move

    movegen = None
    tests_controller = None

    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop("callback", None)
        moves = kwargs.pop("moves", None)
        self.__class__.movegen = None
        super().__init__(*args, **kwargs)
        if moves:
            self.__class__.MOVES = moves

    def handle_game_event(self, event):
        self.__class__.movegen = self.__class__.movegen or self.moves()
        try:
            if event.next_player == self.color:
                move = next(self.__class__.movegen)
                if move:
                    self.controller.handle_gtp_move(self.color, move)
        except StopIteration:
            self.handle_moves_stopped()

    def handle_moves_stopped(self):
        pass


class ControlledGame:
    playercls = MockedPlayer
    controllercls = Controller

    def __init__(self, infos, moves, callback, controllercls=None):
        self.game = Game(**infos)
        self.controller = controllercls(
            black=self.playercls(color=BLACK),
            white=self.playercls(color=WHITE),
            callbacks=self.game.get_callbacks(),
            infos=infos,
        )
        self.callback = callback
        self.game.add_listener(
            self.controller, event_classes=[CursorChanged], wait=True
        )
        for color in (BLACK, WHITE):
            player = self.controller.players[color]
            player.tests_controller = self
            self.game.add_listener(player, event_classes=[CursorChanged])

    def start(self):
        self.game.start()

    def done(self, player):
        self.callback(self)
