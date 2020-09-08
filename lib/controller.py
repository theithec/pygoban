import datetime
import sys
import time

from lib.player import Player
from . import logging
from .board import StonelessReason, StonelessResult
from .game import End, Game, ThreeTimesPassed
from .rulesets import RuleViolation
from .status import BLACK, WHITE, Status
from .timesettings import PlayerTime, TimeSettings
from .coords import array_indexes, sgf_coords


class Controller:
    def __init__(
            self, black: Player, white: Player, game: Game,
            timesettings: TimeSettings = None, *args, **kwargs):
        print("AK", args, kwargs, "g", game)
        super().__init__(*args, **kwargs)
        self.game = game
        self.players = {
            BLACK: black,
            WHITE: white
        }
        timesettings = timesettings or TimeSettings()
        for player in self.players.values():
            player.set_controller(self)
            player.set_timesettings(PlayerTime(player, timesettings))

        self.timeout = False
        self.move_start = None

    def overtime_happend(self, player):
        pass

    def player_lost_by_overtime(self, player):
        raise Exception("TIMEOUT %s" % player.color)

    def set_turn(self, color, result):
        logging.info("SET TURN %s", color)
        nexttime = self.players[color].timesettings.nexttime(start_timer=True)
        logging.info("TIME %s", nexttime)
        self.move_start = datetime.datetime.now()
        self.players[color].set_turn(result)

    def handle_rule_exception(self, exception):
        logging.info(str(exception))

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
                x, y = array_indexes(move, self.game.movetree.board.boardsize)
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
        print("Has turn", color)
        if result:
            print("Last:", result, sgf_coords(result.x, result.y, self.game.boardsize))
        print("Time Black", self.players[BLACK].timesettings)
        print("Time White", self.players[WHITE].timesettings)
        super().set_turn(color, result)
