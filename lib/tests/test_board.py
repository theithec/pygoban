import unittest
from lib.board import Board
from lib.status import BLACK, WHITE


class BoardTest(unittest.TestCase):
    def setUp(self):
        self.board = Board(9)

    def play(self, moves):
        for index, move in enumerate(moves):
            x, y, col_id, killed = move
            # if index == 5:
            #    import pdb; pdb.set_trace()
            result = self.board.result(col_id, x, y)
            self.assertEqual(
                len(result.killed),
                killed,
                "Move %s [%s][%s] %s != %s" % (index, x, y, len(result.killed), killed))

        print(self.board)
        return result

    def test_kill1(self):
        moves = (
            (0, 1, BLACK, 0),
            (0, 0, WHITE, 0),
            (1, 0, BLACK, 1),
            )

        self.play(moves)

    def test_ko(self):

        moves = (
            (0, 1, BLACK, 0),
            (0, 0, WHITE, 0),
            (1, 2, BLACK, 0),
            (1, 1, WHITE, 0),
            (0, 3, BLACK, 0),
            (0, 2, WHITE, 1),
        )

        self.play(moves)

if __name__ == '__main__':
    unittest.main()
