from pygoban.__main__ import startgame, argparse
from pygoban.player import Player
from pygoban.coords import gtp_coords, array_indexes


def moves():
    for move in ("a1", "a2", "a3"):
        yield move


class MockedPlayer(Player):
    movegen = moves()

    def handle_game_event(self, event):
        print("PAT", self.controller.last_result.move.get_path())
        try:
            if event.result.next_player == self.color:
                move = next(self.movegen)
                print("PLAY", move)
                if move:
                    self.controller.handle_gtp_move(self.color, move)
        except StopIteration:
            return
        # print("E", event, event.board)


def test_change_mode(mocker):
    mocker.patch("pygoban.__main__.get_player_cls", return_value=MockedPlayer)
    args = argparse.Namespace(
        boardsize=9,
        nogui=True,
        black_gtp=None,
        white_gtp=None,
        komi=0.5,
        sgf_file=None,
        handicap=0,
        time=None,
    )
    startgame(args, init_gui=False)
