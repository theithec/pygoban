import os
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget
from pygoban.gui.gamewindow import GameWindow
from pygoban.status import BLACK, WHITE
from pygoban.player import Player
from pygoban.events import CursorChanged, MovesReseted, MovePlayed
from pygoban.game import Game


class MockedPlayer(Player):
    MOVES = ("a1", "a2", "a3")

    @classmethod
    def moves(cls):
        for move in cls.MOVES:
            yield move
    movegen = None

    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop("callback", None)
        moves = kwargs.pop("moves", None)
        super().__init__(*args, **kwargs)
        if moves:
            self.__class__.MOVES = moves

    def moves_done(self):
        pass

    def handle_game_event(self, event):
        self.__class__.movegen = self.__class__.movegen or self.moves()
        try:
            if event.next_player == self.color:
                move = next(self.__class__.movegen)
                if move:
                    self.controller.handle_gtp_move(self.color, move)
        except StopIteration:
            self.callback(self)


class ControlledGame:
    playercls = MockedPlayer
    def __init__(self, infos, moves, callback, controllercls=None):
        self.game = Game(**infos)
        callbacks = {
            "get_prisoners": lambda: {BLACK: 0, WHITE: 0},
            "play": self.game.play
        }
        controller = GameWindow(
            black=self.playercls(color=BLACK),
            white=self.playercls(color=WHITE, callback=callback),
            callbacks=callbacks,
            infos=infos
        )
        self.game.add_listener(controller, event_classes=[CursorChanged, MovesReseted])
        for color in (BLACK, WHITE):
            player = controller.players[color]
            self.game.add_listener(player, event_classes=[MovePlayed])
            self.moves_done_signal = player.moves_done_signal

    def start(self, qtbot):
        with qtbot.waitSignal(self.moves_done_signal, timeout=3000):
            self.game.start()
