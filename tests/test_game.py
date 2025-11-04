from pygoban.board import Color, Pos
from pygoban.game import Game
from pygoban.gamecontroller import MainGameController
from pygoban.info import GameInfo

from pygoban.rulesets import Ruleset


def test_game_start(mocker, receiver) -> None:
    mocked_received_node = mocker.patch.object(receiver, "received_turn")
    info = GameInfo()
    ruleset = Ruleset(boardsize=9, komi=0, handicap=0, info=info)
    game = Game(ruleset=ruleset)
    ctrl = MainGameController(game=game)
    ctrl.start(receiver=receiver)
    mocked_received_node.assert_called()
    mocked_received_node.reset_mock()
    ctrl.play(Color.BLACK, Pos(0, 0))
    assert game.nodes.board[0][0].color == Color.BLACK
    mocked_received_node.assert_called()


def test_kill_stone(mocker, receiver) -> None:
    info = GameInfo()
    ruleset = Ruleset(boardsize=9, komi=0, handicap=0, info=info)
    game = Game(ruleset=ruleset)
    ctrl = MainGameController(game=game)
    ctrl.start(receiver=receiver)
