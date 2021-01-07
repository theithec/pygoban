from __future__ import annotations
from dataclasses import dataclass
from threading import Timer

from typing import TYPE_CHECKING
from . import logging

if TYPE_CHECKING:
    from .player import Player


class _PlayerTimer(Timer):
    def __init__(self, nexttime, overtime_callback):
        super().__init__(nexttime, overtime_callback)
        self.start()


@dataclass
class TimeSettings:
    maintime: int = 30
    byoyomi_time: int = 10
    byoyomi_num: int = 3
    byoyomi_stones: int = 1


@dataclass
class Byoyomi:
    time_left: int = 0
    periods_left: int = 0
    stones_left: int = 0


class PlayerTime:
    def __init__(self, player: Player, settings: TimeSettings):
        self.player = player
        self.maintime = settings.maintime
        self.byoyomi = Byoyomi(
            time_left=settings.byoyomi_time,
            periods_left=settings.byoyomi_num,
            stones_left=settings.byoyomi_stones,
        )
        self.byoyomi_time_org = settings.byoyomi_time
        self.byoyomi_stones_org = int(settings.byoyomi_stones)
        self.timer = None

    def cancel_timer(self):
        if self.timer:
            self.timer.cancel()

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
                self.player.lost_by_overtime()
        self.player.controller.period_ended(self.player)
        logging.info("Timeperiod ended %s", self.player)

    def nexttime(self):
        seconds = self.maintime if self.maintime > 0 else self.byoyomi.time_left
        return seconds

    def start_timer(self):
        assert not self.timer or self.timer.finished.is_set(), "T " + str(self.timer)
        self.timer = _PlayerTimer(self.nexttime(), self.period_ended)

    # def subtract_from_now(self, timestamp):
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
        return "{maintime}:{byoyomi.left}x{byoyomi.time}".format(**vars(self))
