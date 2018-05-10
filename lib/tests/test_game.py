import unittest
from lib.game import Game, Player, BLACK, WHITE, RuleViolation


class GameTest(unittest.TestCase):
    def setUp(self):
        black = Player(BLACK)
        white = Player(WHITE)
        self.game = Game(9, black, white)

    def play(self, moves):
        for index, move in enumerate(moves):
            x, y = move
            player = self.game.player()
            self.game.play(player.col_id, x, y)

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
        self.game.undo()
        self.assertEqual(0, self.game.movetree.prisoners[WHITE])
        self.assertEqual(WHITE, self.game.currentcolor)
        with self.assertRaises(RuleViolation):
            self.game.play(BLACK, 3, 3)
