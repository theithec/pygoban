"""Console game"""
from lib.game import BLACK, WHITE, Game
from lib.controller import ConsoleController
from lib.player import ConsolePlayer, GTPPlayer
from lib.rulesets import BaseRuleset

if __name__ == '__main__':
    c = ConsoleController(
        #ConsolePlayer(BLACK),
        GTPPlayer(BLACK, cmd="/usr/games/gnugo --mode gtp"),
        #ConsolePlayer(WHITE),
       #GTPPlayer(WHITE, cmd="/usr/games/gnugo --mode gtp"),
       GTPPlayer(WHITE, cmd="/home/lotek/lib/lizzie/target/katago gtp -model /home/lotek/lib/lizzie/target/g170-b30c320x2-s2846858752-d829865719.bin.gz "),
       game := Game(
        19,
        ruleset_cls=BaseRuleset)).set_turn(BLACK)
    #game.play(BLACK, 6, 2)
    #game.play(BLACK, 6, 6)
    #    #self.do_cmd("play black c7",  False)
    #    #self.do_cmd("play black g7",  False)
    #    #self.do_cmd("play black g3",  False)
    #    #self.do_cmd("play black c3",  False)
