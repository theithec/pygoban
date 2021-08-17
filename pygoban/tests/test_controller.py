import os
from pygoban import startgame, argparse
from pygoban import get_argparser
from pygoban.coords import gtp_coords, array_indexes
from . import MockedPlayer


class MyMockedPlayer(MockedPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = {"sgf": "B[ai];W[ah];B[ag]"}
        self.callback = self.done

    def done(self, player):
        sgf = self.controller.to_sgf().replace(os.linesep, "")
        assert self.result["sgf"] in sgf


def test_change_mode(mocker):
    mocker.patch("pygoban.startgame.get_player_cls", return_value=MyMockedPlayer)
    args = argparse.Namespace(
        boardsize=9,
        nogui=True,
        black_gtp=None,
        black_name="Black",
        white_name="White",
        white_gtp=None,
        komi=0.5,
        sgf_file=None,
        handicap=0,
        time=None,
    )
    game, controller = startgame.startgame(args, init_gui=False)
