import unittest
from pygoban.movetree import MoveTree, Move, BLACK, WHITE
from pygoban.rulesets import RuleViolation
from pygoban.coords import gtp_coords


class MoveTreeTest(unittest.TestCase):
    def setUp(self):
        self.tree = MoveTree(SZ=9)

    def play(self, moves):
        prisoners = moves.pop(0)
        for index, move in enumerate(moves):
            print("I", index, move)
            x, y, col_id = move
            # if index == 5:
            #    import pdb; pdb.set_trace()
            coord = gtp_coords(x, y, 9)
            self.tree.test_move(Move(col_id, coord), apply_result=True)

        self.assertEqual(self.tree.prisoners[BLACK], prisoners[0])
        self.assertEqual(self.tree.prisoners[WHITE], prisoners[1])

        print(self.tree.board)


class MoveTreeMovesTest(MoveTreeTest):
    def test_kill1(self):
        moves = [
            (1, 0),
            (0, 1, BLACK, ),
            (0, 0, WHITE, ),
            (1, 0, BLACK, ),
            ]

        self.play(moves)

    def test_ko(self):

        moves = [
            (0, 1),
            (0, 1, BLACK, ),
            (0, 0, WHITE, ),
            (1, 2, BLACK, ),
            (1, 1, WHITE, ),
            (0, 3, BLACK, ),
            (0, 2, WHITE, ),
        ]

        self.play(moves)

#
#if __name__ == '__main__':
#    unittest.main()
