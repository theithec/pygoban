import datetime
import sys
import time
from typing import Dict, Optional

from .player import Player
from . import logging, InputMode, END_BY_TIME
from .game import MoveResult
from .move import Move
from .status import BLACK, WHITE, Status
from .timesettings import PlayerTime, TimeSettings
from .coords import array_indexes
from .events import CursorChanged, MovesReseted, Counted, Ended
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
        self.input_mode = InputMode.PLAY

    def player_lost_by_overtime(self, player):
        self.end(END_BY_TIME, player.color)

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

    def handle_gtp_move(self, color, move):
        if self.timeout:
            return
        if move == "resign":
            self.callbacks["resign"](color)
        elif move == "pass":
            self.callbacks["pass"](color)
        elif move == "undo":
            self.callbacks["undo"]()
        elif move:
            self.callbacks["play"](color, pos=array_indexes(move, self.infos["SZ"]))

    def update_moves(self, move: Move):
        pass

    def update_board(self, result: MoveResult, board):
        raise NotImplementedError()

    def handle_game_event(self, event):
        if isinstance(event, CursorChanged):
            if not event.result.exception:
                self.last_result: MoveResult = event.result
                self.update_board(event.result, event.board)

                if self.timesettings:
                    self.update_time(event.result.move.color)
                    self.players[event.result.next_player].timesettings.nexttime(
                        start_timer=True
                    )
                    self.move_start = datetime.datetime.now()
        elif isinstance(event, MovesReseted):
            if not self.root:
                self.root = event.root
            self.update_moves(event.root)

        elif isinstance(event, Counted):
            if self.input_mode == InputMode.PLAY:
                self.input_mode = InputMode.COUNT
            self.update_board(event.result, event.board)
        elif isinstance(event, Ended):
            import pudb

            pudb.set_trace()
            self.input_mode = InputMode.COUNT
            self.update_board(event.result, None)

    def to_sgf(self):
        return to_sgf(self.infos, self.root)

    def end(self, reason: str, color: Status):
        logging.info("END: %s", reason.format(color=color))
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
        if isinstance(result, MoveResult):
            print("Last:", result, result.move)
        if self.timesettings:
            print("Time Black", self.players[BLACK].timesettings)
            print("Time White", self.players[WHITE].timesettings)
