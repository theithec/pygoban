from pygoban.status import BLACK
from pygoban.sgf import writer
from pygoban.game import Game
from pygoban import Pos


def test_write():
    game = Game(SZ=9)
    game.play(BLACK, Pos(0, 0))
    sgf = writer.to_sgf(game.infos, game.root)
    assert ";SZ[9]" in sgf
    assert ";B[aa]" in sgf
