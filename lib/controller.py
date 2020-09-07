import sys
import time
import datetime
from . import logging
from .status import Status, BLACK, WHITE
from .rulesets import RuleViolation
from .board import StonelessResult, StonelessReason
from .timesettings import PlayerTime
from .game import ThreeTimesPassed, End


class Controller:
    def __init__(
            self, black, white, game,
            timedata):
        self.game = game
        self.players = {
            BLACK: black,
            WHITE: white
        }
        for player in self.players.values():
            player.set_controller(self)
            player.set_timesettings(PlayerTime(player, timedata))

        self.timeout = False
        self.move_start = None

    def player_lost_by_overtime(self, player):
        raise Exception("TIMEOUT %s" % player.color)
        self.exit()

    def set_turn(self, color, result):
        logging.info("SET TURN %s", color)
        nexttime = self.players[color].timesettings.nexttime(start_timer=True)
        logging.info("TIME %s", nexttime)
        self.move_start = datetime.datetime.now()
        self.players[color].set_turn(result)

    def handle_rule_exception(self, exception):
        logging.info(str(exception))
        # raise exception

    def update_time(self, color, restart=True):
        self.players[color].timesettings.cancel()
        if restart:
            time.sleep(0.2)
            self.players[color].timesettings.nexttime(
                (datetime.datetime.now() - self.move_start).seconds)

    def handle_move(self, color, move):
        if self.timeout:
            return

        if move == "resign":
            self.update_time(color, restart=False)
            self.end(End.RESIGN, color)
        elif move == "pass":
            try:
                self.game.pass_(color)
            except ThreeTimesPassed as err:
                self.end(End.PASSED, err.color)
            self.update_time(color)
            self.set_turn(
                self.game.get_othercolor(color),
                StonelessResult(color, StonelessReason.PASS)
            )
        elif move == "undo":
            self.game.undo(color)
            self.set_turn(
                self.game.get_othercolor(color),
                StonelessResult(color, StonelessReason.UNDO)
            )
        elif move:
            try:
                x, y = self.game.array_indexes(move)
                result = self.game.play(color, x, y)
            except RuleViolation as err:
                self.handle_rule_exception(err)
                return

            self.update_time(color)
            self.set_turn(self.game.get_othercolor(color), result)

    def end(self, reason: End, color: Status):
        for player in self.players.values():
            player.end()

    def exit(self):
        sys.exit()


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
