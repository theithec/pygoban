from pygoban.status import BLACK
from pygoban.sgf import reader


sgf1 = """(;GM[1]FF[4]CA[UTF-8]AP[CGoban:3]ST[2]
RU[Japanese]SZ[19]KM[0.00]
PW[www]PB[bbb]
;B[ab]
;W[aa]
;B[ba]
)
"""


def test_read():
    game = reader.parse(sgf1, {})
    assert game.boardsize == 19
    assert game.prisoners[BLACK] == 1
