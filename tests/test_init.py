from pygoban import get_argparser


def test_argparser():
    parsed = get_argparser().parse_args([])
    assert parsed.sgf_path is None
    assert parsed.black_name is None
    assert parsed.white_name is None
    assert parsed.komi is None
    assert parsed.handicap == 0
    assert parsed.boardsize == 19
    assert parsed.mode == "PLAY"
    assert parsed.time is None

