import pygoban.receivers
from pygoban.board import Color, Pos
from pygoban.game import Game
from pygoban.gamecontroller import GameController
from pygoban.info import GameInfo

# from pygoban.receivers import BaseReceiver
from pygoban.rulesets import Ruleset


def test_game_start(mocker, receiver_cls) -> None:
    info = GameInfo()
    ruleset = Ruleset(boardsize=9, komi=0, handicap=0, info=info)
    game = Game(ruleset=ruleset)
    ctrl = GameController(game=game, receiver_cls=receiver_cls)
    mocked_do_reset = mocker.patch.object(ctrl.receiver, "do_reset")
    ctrl.start()
    for thread in game._event_threads:
        thread.join()
    mocked_do_reset.assert_called()
    mocked_do_stone = mocker.patch.object(ctrl.receiver, "do_stone")
    assert ctrl.callbacks
    ctrl.callbacks.play(Color.BLACK, Pos(0, 0))
    for thread in game._event_threads:
        thread.join()
    assert game.stones.board[0][0].color == Color.BLACK
    mocked_do_stone.assert_called()
