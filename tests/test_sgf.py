from pygoban import Color, Game, NodesController, Pos, coords
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


def test_sgf_properties_are_preserved_and_written():
    ruleset, root = parse(
        "(;GM[1]FF[4]SZ[9]AP[App:1]PL[W]FG[2:Figure]PM[2]VW[aa:bc]"
        ";B[cc]KO[]HO[2]V[-1.5]XX[one][two];PL[B])",
        {},
    )
    move = root.children[0]
    setup = move.children[0]

    assert root.annos.next_player == Color.WHITE
    assert root.annos.sgf_properties["AP"] == ["App:1"]
    assert root.annos.sgf_properties["FG"] == ["2:Figure"]
    assert root.annos.sgf_properties["PM"] == ["2"]
    assert root.annos.sgf_properties["VW"] == ["aa:bc"]
    assert move.annos.sgf_properties["KO"] == [""]
    assert move.annos.sgf_properties["HO"] == ["2"]
    assert move.annos.sgf_properties["V"] == ["-1.5"]
    assert move.annos.sgf_properties["XX"] == ["one", "two"]
    assert setup.annos.next_player == Color.BLACK

    nodes = NodesController(ruleset.boardsize, ruleset.handicap, ruleset.boardheight)
    nodes.root = root
    assert nodes.set_cursor(root).next_color == Color.WHITE
    assert nodes.set_cursor(setup).next_color == Color.BLACK

    serialized = write(root, ruleset)
    for prop in (
        "AP[App:1]",
        "PL[W]",
        "FG[2:Figure]",
        "PM[2]",
        "VW[aa:bc]",
        "KO[]",
        "HO[2]",
        "V[-1.5]",
        "XX[one][two]",
        "PL[B]",
    ):
        assert prop in serialized
