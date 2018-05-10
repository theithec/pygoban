
import unittest
from lib.movetree import MoveTree, BLACK, WHITE
from lib.rulesets import RuleViolation


class MoveTreeTest(unittest.TestCase):
    ruleset = None
    def setUp(self):
        self.tree = MoveTree(boardsize=9, ruleset=self.ruleset)

    def play(self, moves):
        prisoners = moves.pop(0)
        for index, move in enumerate(moves):
            x, y, col_id = move
            # if index == 5:
            #    import pdb; pdb.set_trace()
            self.tree.add(col_id, x, y)

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

class DenyAllRuleset:
    def validate(self, *args, **kwargs):
        raise RuleViolation("BAD")

class MoveTreeRulesetTest(MoveTreeTest):
    ruleset = DenyAllRuleset

    def test_raise(self):
        with self.assertRaises(RuleViolation):
            self.tree.add(BLACK, 0, 0)

if __name__ == '__main__':
    unittest.main()
