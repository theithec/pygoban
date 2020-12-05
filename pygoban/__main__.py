# pylint: disable=import-outside-toplevel, global-statement
# because qt is optional, global is forQApp
import argparse
import signal
import sys

from . import getconfig
from .game import BLACK, WHITE, Game
from .player import GTPPlayer
from .sgf.reader import parse
from .timesettings import TimeSettings
from .events import MovePlayed, CursorChanged, MovesReseted
from .counting import count

signal.signal(signal.SIGINT, signal.SIG_DFL)  # kill with <Ctrl-C>

QAPP = None


def startgame(args: argparse.Namespace, init_gui: bool):
    config = getconfig()
    players = {}

    if args.nogui:
        from .controller import ConsoleController as Controller
        from .player import ConsolePlayer as HumanPlayer
    else:
        from .gui.gamewindow import GameWindow as Controller
        from .gui.player import GuiPlayer as HumanPlayer

    for col, cmd in ((BLACK, args.black_gtp), (WHITE, args.white_gtp)):
        if not cmd:
            players[col] = HumanPlayer(col)
        else:
            players[col] = GTPPlayer(col, cmd=config["GTP"][cmd])

    defaults = {
        "SZ": args.boardsize or config["PYGOBAN"]["boardsize"],
        "KM": args.komi or config["PYGOBAN"]["komi"],
        "RU": "default",
    }
    if args.sgf_file:
        with open(args.sgf_file) as fileobj:
            sgftxt = fileobj.read()
            game = parse(sgftxt, defaults=defaults)
    else:
        game = Game(HA=args.handicap, **defaults)

    callbacks = {
        "play": game.play,
        "get_prisoners": lambda: game.prisoners,
        "set_cursor": game._set_cursor,
        "pass": game.pass_,
        "undo": game.undo,
        "analyze": game.board.analyze,
        "count": lambda: count(game.board),
    }
    controller_kwargs = dict(
        black=players[BLACK],
        white=players[WHITE],
        callbacks=callbacks,
        infos=game.infos,
    )
    if args.time:
        timekwargs = dict(
            zip(
                ("maintime", "byomi_time", "byomi_num", "byomi_stones"),
                [int(arg) for arg in args.time.split(":")],
            )
        )
        controller_kwargs["timesettings"] = TimeSettings(**timekwargs)
    controller = Controller(**controller_kwargs)
    game.add_listener(controller, [CursorChanged, MovesReseted])
    for col in (BLACK, WHITE):
        game.add_listener(players[col], [MovePlayed])

    game.start()

    if not args.nogui:
        controller.setWindowTitle("Pygoban")
        controller.show()
        controller.setMinimumSize(800, 600)

    if init_gui:
        sys.exit(QAPP.exec_())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sgf_file", nargs="?", default=None)
    parser.add_argument("--nogui", action="store_true", help="Show GUI")
    parser.add_argument("--komi", help="komi", type=float)
    parser.add_argument("--black-name", help="Black Name")
    parser.add_argument("--white-name", help="White Name")
    parser.add_argument("--black-gtp", help="Black GTP")
    parser.add_argument("--white-gtp", help="White GTP")
    parser.add_argument("--handicap", help="Handicap", type=int, default=0)
    parser.add_argument("--boardsize", help="Handicap", type=int)
    parser.add_argument(
        "--time", help="[maintime]:[byomi_time]:[byomi_num]:[byomi_stones]"
    )
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


if __name__ == "__main__":
    main()
