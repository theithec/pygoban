import os
import sys
import sysconfig
import configparser
import argparse
import signal

from lib.game import BLACK, WHITE, Game
from lib.rulesets import BaseRuleset
from lib.player import GTPPlayer

signal.signal(signal.SIGINT, signal.SIG_DFL)  # kill with <Ctrl-C>


def writeconfig(config):
    configpath = os.path.sep.join((sysconfig.get_config_var("userbase"), ".pygoban.ini"))
    with open(configpath, "w") as configfile:
        config.write(configfile)


def getconfig():
    config = configparser.ConfigParser()
    config.read(os.path.sep.join((sysconfig.get_config_var("userbase"), ".pygoban.ini")))
    if not config.sections():
        config['PYGOBAN'] = {
            'boardsize': '19',
        }
        writeconfig(config)
    return config


def main():
    config = getconfig()
    parser = argparse.ArgumentParser()
    parser.add_argument("--nogui", action="store_true", help="Show GUI")
    parser.add_argument("--black-gtp", help="Black GTP")
    parser.add_argument("--white-gtp", help="White GTP")
    parser.add_argument("--handicap", help="Handicap", type=int, default=0)
    parser.add_argument("--boardsize", help="Handicap", type=int)
    args = parser.parse_args()
    players = {}

    if args.nogui:
        from lib.controller import ConsoleController as Controller
        from lib.player import ConsolePlayer as HumanPlayer
    else:
        from gui.gamewindow import GameWindow as Controller
        from PyQt5.QtWidgets import QApplication
        from gui.player import GuiPlayer as HumanPlayer
        app = QApplication(sys.argv)

    for col, cmd in ((BLACK, args.black_gtp), (WHITE, args.white_gtp)):
        if not cmd:
            players[col] = HumanPlayer(col)
        else:
            players[col] = GTPPlayer(col, cmd=config["GTP"][cmd])

    boardsize = args.boardsize or config["PYGOBAN"]["boardsize"]
    game = Game(boardsize=boardsize, ruleset_cls=BaseRuleset, handicap=args.handicap)
    controller = Controller(
        black=players[BLACK],
        white=players[WHITE],
        game=game
    )
    if args.nogui:
        controller.set_turn(BLACK)
    else:
        controller.setGeometry(0, 0, 800, 800)
        controller.setWindowTitle('pygoban')
        controller.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
