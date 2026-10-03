from pygoban.board import Color, Pos
from pygoban.game import Game
from pygoban.gamecontroller import MainGameController
from pygoban.info import GameInfo
from pygoban.node import Node
from pygoban.rulesets.japanese import JapaneseRuleset as Ruleset


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


def test_replay_restores_capture_state_and_prisoner_score():
    info = GameInfo()
    ruleset = Ruleset(boardsize=3, komi=0.5, handicap=0, info=info)
    game = Game(ruleset=ruleset)
    nodes = game.nodes
    nodes.root = Node(color=Color.EMPTY)

    moves = (
        (Color.BLACK, Pos(0, 1)),
        (Color.WHITE, Pos(1, 1)),
        (Color.BLACK, Pos(1, 0)),
        (Color.WHITE, None),
        (Color.BLACK, Pos(2, 1)),
        (Color.WHITE, None),
        (Color.BLACK, Pos(1, 2)),
    )
    path = []
    parent = nodes.root
    for color, pos in moves:
        parent = Node(color=color, pos=pos, parent=parent)
        path.append(parent)

    captured_turn = nodes.set_cursor(path[-1])
    assert captured_turn.board.intersection(Pos(1, 1)).color == Color.EMPTY
    assert nodes.total_dead[Color.WHITE] == 1

    before_capture = nodes.set_cursor(path[-2])
    assert before_capture.board.intersection(Pos(1, 1)).color == Color.WHITE
    assert nodes.total_dead[Color.WHITE] == 0

    replayed_capture = nodes.set_cursor(path[-1])
    assert replayed_capture.board.intersection(Pos(1, 1)).color == Color.EMPTY
    assert nodes.total_dead[Color.WHITE] == 1
    assert ruleset.count()["black"].prisoners == 1
