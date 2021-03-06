# pylint: disable=import-outside-toplevel, global-statement
# because qt is optional, global is forQApp
import argparse
import sys

from . import getconfig, get_argparser
from .game import BLACK, WHITE, Game
from .player import GTPPlayer
from .sgf.reader import parse
from .timesettings import TimeSettings
from .events import MovePlayed, CursorChanged, MovesReseted, Counted, Ended
QAPP = None
GAME_WINDOWS = []
"""No usage but avoiding garbage collection"""


def get_control_cls(nogui):
    if nogui:
        from .controller import ConsoleController as Controller
    else:
        from .gui.gamewindow import GameWindow as Controller
    return Controller


def get_player_cls(nogui):
    if nogui:
        from .player import ConsolePlayer as HumanPlayer
    else:
        from .gui.player import GuiPlayer as HumanPlayer
    return HumanPlayer


def startgame(args: argparse.Namespace, init_gui: bool, root=None):
    config = getconfig()
    players = {}
    controller_cls = get_control_cls(args.nogui)
    player_cls = get_player_cls(args.nogui)
    for col, name, cmd in (
        (BLACK, args.black_name, args.black_gtp),
        (WHITE, args.white_name, args.white_gtp),
    ):
        if not cmd:
            players[col] = player_cls(col, name=name)
        else:
            players[col] = GTPPlayer(col, name=name, cmd=config["GTP"][cmd])

    defaults = {
        "SZ": args.boardsize or int(config["PYGOBAN"]["boardsize"]),
        "KM": args.komi or config["PYGOBAN"]["komi"],
        "RU": "default",
        "PB": args.black_name,
        "PW": args.white_name,
        "GN": "-".join([players[col].name for col in (BLACK, WHITE)]),
    }
    if args.sgf_file:
        with open(args.sgf_file) as fileobj:
            sgftxt = fileobj.read()
            game = parse(sgftxt, defaults=defaults)
            for color, key in ((BLACK, "PB"), (WHITE, "PW")):
                players[color].name = game.infos.get(key, players[color].name)
        args.mode = "EDIT"
    else:
        game = Game(HA=args.handicap, **defaults)

    controller_kwargs = dict(
        black=players[BLACK],
        white=players[WHITE],
        callbacks=game.get_callbacks(),
        infos=game.infos,
        mode=args.mode,
    )
    if args.time:
        timekwargs = dict(
            zip(
                ("maintime", "byoyomi_time", "byoyomi_num", "byoyomi_stones"),
                [int(arg) for arg in args.time.split(":")],
            )
        )
        controller_kwargs["timesettings"] = TimeSettings(**timekwargs)
    controller = controller_cls(**controller_kwargs)
    game.add_listener(
        controller, [CursorChanged, MovesReseted, Counted, Ended], wait=True
    )
    for col in (BLACK, WHITE):
        game.add_listener(players[col], [MovePlayed, Counted])
    if root:
        game.root = root

    if not args.nogui:
        controller.setMinimumSize(800, 600)
        controller.show()
        controller.activateWindow()
        GAME_WINDOWS.append(controller)

    game.start()
    if init_gui:
        sys.exit(QAPP.exec_())

    # For testing
    return game, controller

def startpygoban():
    parser = get_argparser()
    args = parser.parse_args()
    if not args.nogui:
        from PyQt5.QtWidgets import QApplication

        global QAPP
        QAPP = QApplication([])
        if not any((args.sgf_file, args.boardsize, args.black_gtp, args.white_gtp)):
            from .gui.startwindow import StartWindow

            win = StartWindow(parser, starter_callback=startgame)
            win.show()
            sys.exit(QAPP.exec_())
        startgame(args, init_gui=True)
    else:
        startgame(args, init_gui=False)
