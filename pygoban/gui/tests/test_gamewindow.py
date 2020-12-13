import os
import pytest
from pytestqt.exceptions import TimeoutError
from pygoban.gui.gamewindow import GameWindow
from pygoban.gui.tests import QontrolledGame


def _test_gamewindow(qtbot, moves, done):
    cog = QontrolledGame(
        infos={
            "SZ": 9,
            "RU": "japanese",
        },
        moves=moves,
        callback=done,
        controllercls=GameWindow,
    )
    cog.start(qtbot)


def test_gamewindow_moves_to_sgf(qtbot):
    moves = ("a1", "a2", "a3")
    result = {"sgf": "B[ai];W[ah];B[ag]"}

    def done(player):
        sgf = player.controller.to_sgf().replace(os.linesep, "")
        assert result["sgf"] in sgf
        assert len(player.controller.guiboard.intersections) == 81

    _test_gamewindow(qtbot, moves, done)


def test_gamewindow_intersections_failure(qtbot):
    def done(player):
        assert len(player.controller.guiboard.intersections) == 82

    moves = []
    with pytest.raises(TimeoutError):
        _test_gamewindow(qtbot, moves, done)


def test_gamewindow_intersections_ok(qtbot):
    def done(player):
        assert len(player.controller.guiboard.intersections) == 81

    moves = []
    _test_gamewindow(qtbot, moves, done)
