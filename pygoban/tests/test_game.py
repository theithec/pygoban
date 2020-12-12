import unittest
from pygoban.status import BLACK, WHITE, EMPTY
from pygoban.game import Game
from pygoban.controller import Controller
from pygoban.player import Player
from pygoban.rulesets import BaseRuleset, RuleViolation, KoViolation, OccupiedViolation
from pygoban.coords import gtp_coords
from pygoban.move import Empty


class BaseGameTest(unittest.TestCase):
    ruleset_cls = BaseRuleset

    def setUp(self):
        self.game = Game(SZ=9)

    def play_move(self, x, y, color=None):
        color = color or self.game.nextcolor
        result = self.game.play(color=color, pos=(x, y))
        if result.exception is not None:
            print("RAISE", result.exception)
            raise result.exception

    def play_moves(self, moves):
        for index, move in enumerate(moves):
            x, y = move
            self.play_move(x, y, color=self.game.nextcolor)


class GameTest(BaseGameTest):
    ruleset_cls = BaseRuleset

    def test_kill1(self):
        moves = (
            (
                0,
                1,
            ),
            (
                0,
                0,
            ),
            (
                1,
                0,
            ),
        )

        self.play_moves(moves)
        self.assertEqual(1, self.game.prisoners[BLACK])

    def test_ko(self):

        moves = (
            (
                0,
                1,
            ),
            (
                0,
                0,
            ),
            (
                1,
                2,
            ),
            (
                1,
                1,
            ),
            (
                0,
                3,
            ),
            (
                0,
                2,
            ),
        )

        self.play_moves(moves)
        self.assertEqual(1, self.game.prisoners[WHITE])
        # now is ko
        with self.assertRaises(KoViolation):
            self.play_move(0, 1, BLACK)

        self.assertEqual(BLACK, self.game.nextcolor)

        self.play_moves(((4, 4), (5, 5), (0, 1)))
        self.assertEqual(1, self.game.prisoners[BLACK])

        self.play_move(6, 6, WHITE)
        self.play_move(7, 7, BLACK)
        self.play_move(0, 2, WHITE)
        self.assertEqual(2, self.game.prisoners[WHITE])

        self.game.undo()
        self.assertEqual(1, self.game.prisoners[WHITE])

    def test_occupied(self):
        self.play_move(
            4,
            4,
            BLACK,
        )
        with self.assertRaises(OccupiedViolation):
            self.play_move(4, 4, WHITE)

        self.assertEqual(WHITE, self.game.nextcolor)

    def test_undo(self):
        moves = (
            (0, 0),
            (0, 1),
            (1, 1),
            (0, 2),
            (1, 2),
            (3, 3),
            (0, 3),
        )
        self.play_moves(moves)
        self.assertEqual(2, self.game.prisoners[BLACK])

        self.assertEqual(WHITE, self.game.nextcolor)
        self.game.undo()
        self.assertEqual(BLACK, self.game.nextcolor)
        self.assertEqual(0, self.game.prisoners[BLACK])
        self.game.undo()
        self.assertEqual(EMPTY, self.game.board[3][3])
        self.assertEqual(WHITE, self.game.nextcolor)

    def test_pass(self):
        self.game.play(BLACK, (0, 1))
        self.game.play(WHITE, Empty.PASS)
        self.game.play(BLACK, (0, 2))


class DenyAllRuleset(BaseRuleset):
    def validate(self, *args, **kwargs):
        raise RuleViolation("BAD")


class DeynAllRulesetTest(BaseGameTest):
    def test_raise(self):
        self.game.ruleset = DenyAllRuleset(self.game)
        moves = (
            (
                0,
                1,
            ),
        )
        with self.assertRaises(RuleViolation):
            self.play_moves(moves)
