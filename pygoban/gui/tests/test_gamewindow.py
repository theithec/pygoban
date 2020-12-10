import os
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget
from pygoban.gui.gamewindow import GameWindow
from pygoban.status import BLACK, WHITE
from pygoban.player import Player
from pygoban.events import CursorChanged, MovesReseted, MovePlayed
from pygoban.game import Game
from pygoban.tests import ControlledGame
from pygoban.gui.tests import QTestPlayer, QontrolledGame


def test_gamewindow(qtbot):

    MOVES = ("a1", "a2", "a3")
    result = {"sgf": "B[ai];W[ah];B[ag]"}

    def done(player):
        sgf = player.controller.to_sgf().replace(os.linesep, "")
        assert result["sgf"] in sgf
        assert len(player.controller.guiboard.intersections) == 81

    cog = QontrolledGame(
        infos= {
            "SZ": 9,
            "RU": "japanese",
        },
        moves=MOVES,
        callback=done,
        controllercls=GameWindow
    )
    cog.start(qtbot)
