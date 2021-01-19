import datetime
import sys
import time
from typing import Dict, Optional

from .player import Player
from . import logging, InputMode, END_BY_TIME
from .game import MoveResult
from .move import Empty
from .status import BLACK, WHITE, Status, get_othercolor
from .timesettings import PlayerTime, TimeSettings
from .coords import array_indexes
from .events import CursorChanged, Counted, Ended
from .sgf.writer import to_sgf


# pylint: disable=no-self-use
class Controller:
    def __init__(
        self,
        black: Player,
        white: Player,
        callbacks: Dict,
        infos: Dict,
        mode="PLAY",
        timesettings: TimeSettings = None,
    ):
        self.players = {BLACK: black, WHITE: white}
        self.timesettings = timesettings
        self.callbacks = callbacks
        self.infos = infos
        for player in self.players.values():
            player.set_controller(self)
            if self.timesettings:
                player.set_clock(PlayerTime(player, self.timesettings))

        self.move_start = None
        self.last_move_result: Optional[CursorChanged] = None
        # self.count: Optional[Counted] = None
        self.root = None
        self.mode = mode
        self.input_mode = InputMode.PLAY
        self.ended = False

    def player_lost_by_overtime(self, player):
        self.end(END_BY_TIME, get_othercolor(player.color))

    def handle_rule_exception(self, exception):
        logging.info(str(exception))

    def update_time(self, event):
        self.move_start = self.move_start or datetime.datetime.now()
        if (color := event.cursor.color) in (BLACK, WHITE):
            self.players[color].clock.subtract(
                (datetime.datetime.now() - self.move_start).seconds
            )
            self.players[color].clock.cancel_timer()
        time.sleep(0.2)
        self.move_start = datetime.datetime.now()
        self.players[event.next_player].clock.start_timer()

    def handle_gtp_move(self, color, move):
        if move in ("resign", "pass", "undo"):
            pos = Empty[move.upper()]
        else:
            pos = array_indexes(move, self.infos["SZ"])
        self._play(color, pos)

    def game_callback(self, name, *args, **kwargs):
        self.callbacks[name](*args, **kwargs)

    def update_board(self, event: CursorChanged, board):
        raise NotImplementedError()

    def period_ended(self, player):
        self.move_start = datetime.datetime.now()

    def _play(self, color, pos):
        self.game_callback("play", color=color, pos=pos)

    def handle_game_event(self, event):
        if isinstance(event, CursorChanged):
            self.last_move_result: MoveResult = event
            if event.cursor.is_root:
                self.root = event.cursor
            if self.timesettings:
                self.update_time(event)
            self.update_board(event, event.board)

        elif isinstance(event, Counted):
            self.update_board(event, event.board)

        elif isinstance(event, Ended):
            self.input_mode = InputMode.ENDED
            self.update_board(event, None)

    def to_sgf(self):
        return to_sgf(self.infos, self.root)

    def end(self, reason: str, color: Status):
        self.infos["RE"] = f"{color.shortval}+{reason}"
        logging.info("END: %s", reason.format(color=color))
        self.ended = True
        for player in self.players.values():
            player.end()

    def exit(self):
        sys.exit()


class ConsoleController(Controller):
    def update_board(self, event, board=None):
        print(event.board)
        print(
            "\n".join(
                [
                    f"{key} caught\t{val}"
                    for key, val in self.callbacks["get_prisoners"]().items()
                ]
            )
        )
        if isinstance(event, MoveResult):
            print("Last:", event, event.move)
        if self.timesettings:
            print("Time Black", self.players[BLACK].clock)
            print("Time White", self.players[WHITE].clock)
