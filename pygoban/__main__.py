import sys
import argparse
import signal

from . import getconfig
from .game import BLACK, WHITE, Game
from .rulesets import BaseRuleset
from .player import GTPPlayer
from .sgf import parse
from .timesettings import TimeSettings


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

    boardsize = args.boardsize or config["PYGOBAN"]["boardsize"]
    game = Game(boardsize=boardsize, ruleset_cls=BaseRuleset, handicap=args.handicap)
    if args.sgf_file:
        with open(args.sgf_file) as fileobj:
            sgftxt = fileobj.read()
            tree = parse(sgftxt)
        game._movetree = tree

    controller_kwargs = dict(
        black=players[BLACK],
        white=players[WHITE],
        game=game
    )
    if args.time:
        timekwargs = dict(zip(
            ("maintime", "byomi_time", "byomi_num", "byomi_stones"),
            [int(arg) for arg in args.time.split(":")]))
        controller_kwargs["timesettings"] = TimeSettings(**timekwargs)
    controller = Controller(**controller_kwargs)
    if args.nogui:
        controller.set_turn(game.currentcolor)
    else:
        controller.setWindowTitle('pygoban')
        controller.show()
        controller.setMinimumSize(800, 600)

    if init_gui:
        sys.exit(QAPP.exec_())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sgf_file', nargs='?', default=None)
    parser.add_argument("--nogui", action="store_true", help="Show GUI")
    parser.add_argument("--black-gtp", help="Black GTP")
    parser.add_argument("--white-gtp", help="White GTP")
    parser.add_argument("--handicap", help="Handicap", type=int, default=0)
    parser.add_argument("--boardsize", help="Handicap", type=int)
    parser.add_argument("--time", help="[maintime]:[byomi_time]:[byomi_num]:[byomi_stones]")
    args = parser.parse_args()
    if not args.nogui:
        from PyQt5.QtWidgets import QApplication
        global QAPP
        QAPP = QApplication([])
        if not args.sgf_file and not args.boardsize:
            from .gui.startwindow import StartWindow
            win = StartWindow(parser, starter_callback=startgame)
            win.show()
            sys.exit(QAPP.exec_())
        startgame(args, init_gui=True)
    else:
        startgame(args, init_gui=False)


if __name__ == "__main__":
    main()
