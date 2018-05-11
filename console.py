from lib import BLACK, WHITE
from lib.player import ConsolePlayer, ThreadPlayer
from lib.game import Game
from lib.observer import ConsoleObserver
from lib.rulesets import BaseRuleset


if __name__ == '__main__':
    Game(9, ConsolePlayer(BLACK),
            #ConsolePlayer(WHITE),
            ThreadPlayer(WHITE, cmd="/usr/games/gnugo --mode gtp"),
            ruleset_cls=BaseRuleset, observer_cls=ConsoleObserver)
