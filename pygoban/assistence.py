from copy import copy
from .controller import ControllerMixin as Controller
from .move import Empty
from .events import CursorChanged
from .startgame import initgame
from .player import PassingPlayer, GTPPlayer
from . import logging, InputMode, getconfig
from .status import BLACK, WHITE, Status, get_othercolor


class Assistent(Controller):
    def __init__(self, gtp_name: str, orig: Controller, *args, **kwargs):
        self.gtp_name = gtp_name
        self.orig = orig
        super().__init__(*args, **kwargs)

    def handle_game_event(self, event):
        logging.debug("Asi handle: %s (%s)", self, event)
        if isinstance(event, CursorChanged) and event.cursor.pos == Empty.PASS:
            tip = event.cursor.parent
            print("TIPP", tip)
            self.orig.last_move_result.cursor.extras.decorations[tip.pos] = "*"
            self.orig.guiboard.repaint()


def assist(cmd, orig: Controller):
    assert orig.last_move_result
    col = orig.last_move_result.next_player
    assert col
    config = getconfig()
    players = {
        col: GTPPlayer(col, cmd, cmd=config["GTP"][cmd]),
        get_othercolor(col): PassingPlayer(get_othercolor(col)),
    }
    g, c = initgame(
        controller_cls=Assistent,
        nogui=True,
        root=copy(orig.root),
        input_mode=InputMode.EDIT,
        players=players,
        extra_controller_kwargs={"orig": orig, "gtp_name": "gnugo"},
    )
    c.input_mode = InputMode.EDIT
    path = orig.last_move_result.cursor.get_path()
    for col in (BLACK, WHITE):
        c.players[col].moves = [move for move in path if move.color == col]
    g.start()
