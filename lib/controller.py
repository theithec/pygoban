import datetime
from . import logging
from .status import BLACK, WHITE
from .rulesets import RuleViolation
from .board import StonelessResult
from .timesettings import TimeSettings


class Controller:
    def __init__(
            self, black, white, game,
            maintime=10, byomi_time=5, byomi_num=3, byomi_stones=1):
        self.game = game
        self.players = {
            BLACK: black,
            WHITE: white
        }
        for player in self.players.values():
            player.set_controller(self)
            player.set_timesettings(TimeSettings(
                player,
                maintime=maintime, byomi_time=byomi_time,
                byomi_num=byomi_num, byomi_stones=byomi_stones))

        self.timeout = False
        self.move_start = None
        self.pass_cnt = 0

    def player_lost_by_overtime(self, player):
        raise Exception("TIMEOUT %s" % player.color)
        self.exit()

    def set_turn(self, color, result):
        logging.info("SET TURN %s", color)
        nexttime = self.players[color].timesettings.nexttime(start_timer=True)
        logging.info("TIME %s", nexttime)
        self.move_start = datetime.datetime.now()
        self.players[color].set_turn(result)


    def handle_exception(self, exception):
        logging.info(str(exception))
        raise exception

    def handle_move(self, color, move):
        if self.timeout:
            return
        if self.pass_cnt > 2:
            print("#3 x PASSED")
            self.exit()
            return
        if not self.game.currentcolor == color:
            self.handle_exception(RuleViolation(
                "Wrong player %s %s", str(color), str(self.game.currentcolor)))
            return

        self.players[color].timesettings.cancel()

        if move == "resign":
            self.exit()
            return
        if move == "pass":
            self.game._pass(color)
            self.pass_cnt += 1
            self.set_turn(
                self.game.get_othercolor(color),
                StonelessResult(color, "pass")
            )
            return
        else:
            self.pass_cnt = 0

        self.players[color].timesettings.cancel()
        self.players[color].timesettings.nexttime(
            (datetime.datetime.now() - self.move_start).seconds)
        if move == "undo":
            self.game.undo(color)
            self.set_turn(
                self.game.get_othercolor(color),
                StonelessResult(color, "undo")
            )
            self.players[color].timesettings.cancel()
        elif move:
            try:
                x, y = self.game.array_indexes(move)
                result = self.game.play(color, x, y)
            except RuleViolation as err:
                self.handle_exception(err)

            self.set_turn(self.game.get_othercolor(color), result)

    def exit(self):
        for player in self.players.values():
            player.end()


class ConsoleController(Controller):

    def set_turn(self, color, result=None):
        print(self.game.movetree.board)
        print("\n".join([
            f"{key} caught\t{val}" for key, val in self.game.movetree.prisoners.items()]))
        print("Has turn", color),
        if result:
            print("Last:", result, self.game.sgf_coords(result.x, result.y))
        print("Time Black", self.players[BLACK].timesettings)
        print("Time White", self.players[WHITE].timesettings)
        super().set_turn(color, result)
