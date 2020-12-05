from dataclasses import dataclass
from threading import Timer
from .player import Player

from . import logging


class _PlayerTimer(Timer):
    def __init__(self, nexttime, overtime):
        logging.info("START CLOCK %s", nexttime)
        super().__init__(nexttime, overtime)
        self.start()


@dataclass
class TimeSettings:
    maintime: int = 10
    byomi_time: int = 5
    byomi_num: int = 3
    byomi_stones: int = 1


@dataclass
class Byomi:
    time: int = 0
    left: int = 0
    stones: int = 0


class PlayerTime:
    def __init__(self, player: Player, settings: TimeSettings):
        self.player = player
        self.maintime = settings.maintime
        self.byomi = Byomi(
            time=settings.byomi_time,
            left=settings.byomi_num,
            stones=settings.byomi_stones,
        )

        self.byomi_time_org = settings.byomi_time
        self.byomi_stones_org = settings.byomi_stones
        self.timer = None

    def cancel(self):
        logging.info("CANCEL CLOCK")
        if self.timer:
            self.timer.cancel()

    def period_ended(self):
        logging.info("Timeperiod ended %s", self)
        self.cancel()
        if self.maintime > 0:
            self.maintime = 0
        else:
            self.byomi.left -= 1

        if self.byomi.left > 0:
            self.byomi.time = self.byomi_time_org
            self.nexttime(start_timer=True)
        else:
            self.player.lost_by_overtime()
        self.player.controller.period_ended(self.player)

    def nexttime(self, used=0, start_timer=False):
        logging.info("nexttime(%s): %s", start_timer, self.player)
        _next = 0
        if self.maintime > 0:
            self.maintime -= used
            _next = self.maintime
        else:
            self.byomi.stones -= 1
            if self.byomi.stones > 0:
                self.byomi.time -= used
            else:
                self.byomi.time = self.byomi_time_org
            if self.byomi.left > 0:
                _next = self.byomi.time
        if start_timer:
            assert not self.timer or self.timer.finished.is_set(), "T " + str(
                self.timer
            )
            self.timer = _PlayerTimer(_next, self.period_ended)
        return _next

    def __str__(self):
        return "{maintime}:{byomi.left}x{byomi.time}".format(**vars(self))
