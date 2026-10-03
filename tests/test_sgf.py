from pygoban import Color, Game, Pos, coords
from pygoban.sgf.reader import parse
from pygoban.sgf.writer import write


def test_rectangular_board_sgf_round_trip():
    ruleset, root = parse("(;GM[1]FF[4]SZ[9:13];B[ia])", {})

    assert (ruleset.boardsize, ruleset.boardheight) == (9, 13)
    assert (len(Game(ruleset).nodes.board), len(Game(ruleset).nodes.board[0])) == (
        9,
        13,
    )
    assert root.children[0].pos == Pos(8, 0)
    assert root.children[0].color == Color.BLACK

    serialized = write(root, ruleset)
    assert "SZ[9:13]" in serialized
    reparsed_ruleset, _ = parse(serialized, {})
    assert (reparsed_ruleset.boardsize, reparsed_ruleset.boardheight) == (9, 13)


def test_sgf_coordinates_support_uppercase_range():
    pos = coords.sgf_to_pos("AZ")

    assert pos == Pos(26, 51)
    assert coords.pos_to_sgf(pos) == "AZ"


def test_sgf_board_size_default_remains_square():
    ruleset, _ = parse("(;GM[1]FF[4])", {})

    assert (ruleset.boardsize, ruleset.boardheight) == (19, 19)