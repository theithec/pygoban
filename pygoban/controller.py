import datetime
import sys
import time
from typing import Dict, Optional

from .player import Player
from . import logging
from .game import End, ThreeTimesPassed, MoveResult
from .move import Move
from .rulesets import RuleViolation
from .status import BLACK, WHITE, Status
from .timesettings import PlayerTime, TimeSettings
from .coords import array_indexes
from .events import CursorChanged, MovesReseted
from .sgf.writer import to_sgf


# pylint: disable=no-self-use
class Controller:
    def __init__(
        self,
        black: Player,
        white: Player,
        callbacks: Dict,
        infos: Dict,
        timesettings: TimeSettings = None,
    ):
        # self.game = game
        self.players = {BLACK: black, WHITE: white}
        self.timesettings = timesettings
        self.callbacks = callbacks
        self.infos = infos
        for player in self.players.values():
            player.set_controller(self)
            if self.timesettings:
                player.set_timesettings(PlayerTime(player, self.timesettings))

        self.timeout = False
        self.move_start = None
        self.last_result: Optional[MoveResult] = None
        self.root = None

    def player_lost_by_overtime(self, player):
        self.end(End.BY_TIME, player.color)

    def handle_rule_exception(self, exception):
        logging.info(str(exception))

    def update_time(self, color, restart=True):
        if color in (BLACK, WHITE):
            self.players[color].timesettings.cancel()
            if restart:
                time.sleep(0.2)
                self.players[color].timesettings.nexttime(
                    (datetime.datetime.now() - self.move_start).seconds
                )

    def handle_move(self, color, move):
        if self.timeout:
            return
        if move == "resign":
            if self.timesettings:
                self.update_time(color, restart=False)
            self.end(End.RESIGN, color)
        elif move == "pass":
            try:
                self.callbacks["pass"](color)
            except ThreeTimesPassed as err:
                self.end(End.PASSED, err.args[0])
            # if self.timesettings:
            #    self.update_time(color)
        elif move == "undo":
            self.callbacks["undo"]()
        elif move:
            try:
                self.callbacks["play"](color, pos=array_indexes(move, self.infos["SZ"]))
            except RuleViolation as err:
                self.handle_rule_exception(err)

    def count(self):
        self.callbacks["count"]()

    def update_moves(self, move: Move):
        pass

    def update_board(self, result: MoveResult, board):
        raise NotImplementedError()

    def handle_game_event(self, event):
        if isinstance(event, CursorChanged):
            self.last_result: MoveResult = event.result
            self.update_board(event.result, event.board)

            if self.timesettings:
                self.update_time(event.result.move.color)
                self.players[event.result.next_player].timesettings.nexttime(
                    start_timer=True
                )
                self.move_start = datetime.datetime.now()
        if isinstance(event, MovesReseted):
            if not self.root:
                self.root = event.root
            self.update_moves(event.root)

        # if self.root:
        #     print("SGF:\n", self.to_sgf())

    def to_sgf(self):
        return to_sgf(self.infos, self.root)

    def end(self, reason: End, color: Status):
        logging.info("END: %s %s", reason, color)
        self.timeout = True
        for player in self.players.values():
            player.end()

    def exit(self):
        sys.exit()


class ConsoleController(Controller):
    def update_board(self, result, board=None):
        print(
            "\n".join(
                [
                    f"{key} caught\t{val}"
                    for key, val in self.callbacks["get_prisoners"]().items()
                ]
            )
        )
        color = self.callbacks["get_next_color"]()
        print("Has turn", color)
        if result:
            print("Last:", result, result.move)
        if self.timesettings:
            print("Time Black", self.players[BLACK].timesettings)
            print("Time White", self.players[WHITE].timesettings)
