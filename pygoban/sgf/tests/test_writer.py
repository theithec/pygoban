from pygoban.status import BLACK
from pygoban.sgf import reader


def test_write():
    game = reader.parse(sgf1, {})
    assert game.boardsize == 19
    assert game.prisoners[BLACK] == 1
