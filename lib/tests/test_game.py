import unittest
from lib import BLACK, WHITE, EMPTY
from lib.game import Game
from lib.player import Player
from lib.rulesets import BaseRuleset, RuleViolation, KoViolation, OccupiedViolation


class BaseGameTest(unittest.TestCase):
    ruleset_cls = None

    def setUp(self):
        black = Player(BLACK)
        white = Player(WHITE)
        self.game = Game(9, black, white, ruleset_cls=self.ruleset_cls)

    def play(self, moves):
        for index, move in enumerate(moves):
            x, y = move
            player = self.game.player()
            self.game.play(player.col_id, x, y)


class GameTest(BaseGameTest):
    ruleset_cls = BaseRuleset

    def test_kill1(self):
        moves = (
            (0, 1, ),
            (0, 0, ),
            (1, 0, ),
            )

        self.play(moves)
        self.assertEqual(1, self.game.movetree.prisoners[BLACK])

    def test_ko(self):

        moves = (
            (0, 1, ),
                (0, 0, ),
            (1, 2, ),
                (1, 1, ),
            (0, 3, ),
                (0, 2, ),
        )

        self.play(moves)
        self.assertEqual(1, self.game.movetree.prisoners[WHITE])
        # now is ko
        with self.assertRaises(KoViolation):
            self.game.play(BLACK, 0, 1)

        self.assertEqual(BLACK, self.game.currentcolor)

        self.game.play(BLACK, 4, 4)
        self.game.play(WHITE, 5, 5)
        self.game.play(BLACK, 0, 1)
        self.assertEqual(1, self.game.movetree.prisoners[BLACK])

        self.game.play(WHITE, 6, 6)
        self.game.play(BLACK, 7, 7)
        self.game.play(WHITE, 0, 2)
        self.assertEqual(2, self.game.movetree.prisoners[WHITE])

        self.game.undo()
        self.assertEqual(1, self.game.movetree.prisoners[WHITE])

    def test_occupied(self):
        self.game.play(BLACK, 4, 4)
        with self.assertRaises(OccupiedViolation):
            self.game.play(WHITE, 4, 4)

        self.assertEqual(WHITE, self.game.currentcolor)

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
        self.play(moves)
        self.assertEqual(2, self.game.movetree.prisoners[BLACK])
        self.game.undo()
        self.assertEqual(BLACK, self.game.currentcolor)
        self.assertEqual(0, self.game.movetree.prisoners[BLACK])
        self.game.undo()
        self.assertEqual(EMPTY, self.game.movetree.board[3][3])
        self.assertEqual(WHITE, self.game.currentcolor)


class DenyAllRuleset(BaseRuleset):
    def validate(self, *args, **kwargs):
        raise RuleViolation("BAD")


class DeynAllRulesetTest(BaseGameTest):
    ruleset_cls = DenyAllRuleset

    def test_raise(self):
        moves = ((0, 1, ),)
        with self.assertRaises(RuleViolation):
            self.play(moves)
