from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from threading import Timer
from typing import TYPE_CHECKING

from pygoban.results import TurnDone

if TYPE_CHECKING:
    from pygoban.board import Color
    from pygoban.game import Game


class _PlayerTimer(Timer):
    def __init__(self, nexttime, overtime_callback):
        super().__init__(nexttime, overtime_callback)
        self.start()


@dataclass
class TimeSettings:
    maintime: int = 10
    byoyomi_time: int = 10
    byoyomi_num: int = 3
    byoyomi_stones: int = 1


@dataclass
class Byoyomi:
    time_left: int = 0
    periods_left: int = 0
    stones_left: int = 0


class PlayerTime:
    def __init__(self, game: "Game", color: "Color"):
        self.game = game
        self.color = color
        settings = game.ruleset.timesettings
        assert settings
        self.maintime = settings.maintime
        self.byoyomi = Byoyomi(
            time_left=settings.byoyomi_time,
            periods_left=settings.byoyomi_num,
            stones_left=settings.byoyomi_stones,
        )
        self.byoyomi_time_org = settings.byoyomi_time
        self.byoyomi_stones_org = int(settings.byoyomi_stones)
        self.timer = None
        self.last_started = None
        self.ended = False
        # self.first_time = True

    def start_timer(self):
        print("START TIMER", self.color, self)
        assert not self.ended
        self.last_started = datetime.now()
        self.timer = _PlayerTimer(self.nexttime(), self.period_ended)

    def cancel_timer(self):
        print("CANCEL TIMER", self.color, self)
        if self.timer:
            self.timer.cancel()
        if self.last_started:
            subtrahend = (datetime.now() - self.last_started).seconds
            self.subtract(subtrahend)
        return self.nexttime()

    def period_ended(self):
        self.cancel_timer()

        if self.maintime > 0:
            self.maintime = 0
        else:
            self.byoyomi.periods_left -= 1

        if self.maintime == 0:
            if self.byoyomi.periods_left > 0:
                self.byoyomi.time_left = self.byoyomi_time_org
                self.start_timer()
            else:
                self.byoyomi.time_left = 0
                self.ended = True
        self.game.period_ended(self.color, self.nexttime())
        logging.info("Timeperiod ended %s", self.color)

    def nexttime(self):
        seconds = self.maintime if self.maintime > 0 else self.byoyomi.time_left
        return seconds

    def subtract(self, seconds: int):
        if self.maintime > 0:
            self.maintime -= seconds
        else:
            self.byoyomi.stones_left -= 1
            if self.byoyomi.stones_left > 0:
                self.byoyomi.time_left -= seconds
            else:
                self.byoyomi.time_left = self.byoyomi_time_org
                self.byoyomi.stones_left = self.byoyomi_stones_org

    def __str__(self):
        return f"Timer {self.color} "
