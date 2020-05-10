import sys
from threading import Timer

from . import logging


class GameClock(Timer):
    def __init__(self, nexttime, overtime):
        logging.info("START CLOCK %s", nexttime)
        super().__init__(nexttime, overtime)
        self.start()


class TimeSettings:
    def __init__(self, player, maintime, byomi_time, byomi_num, byomi_stones=1):
        self.player = player
        self.maintime = maintime
        self.byomi_time = byomi_time
        self.byomi_time_org = byomi_time
        self.byomi_num = byomi_num
        self.byomi_stones = byomi_stones
        self.byomi_stones_org = byomi_stones
        self.timer = None

    def cancel(self):
        logging.info("CANCEL CLOCK")
        if self.timer:
            self.timer.cancel()

    def overtime(self, used=0):
        logging.info("OVERTIME %s", self)
        self.cancel()
        if self.maintime > 0:
            self.maintime = 0
        else:
            self.byomi_num -= 1

        if self.byomi_num > 0:
            self.byomi_time = self.byomi_time_org
            return self.nexttime(start_timer=True)
        else:
            self.player.lost_by_overtime()

    def nexttime(self, used=0, start_timer=False):
        _next = 0
        if self.maintime > 0:
            self.maintime -= used
            _next = self.maintime
        else:
            self.byomi_stones -= 1
            if self.byomi_stones > 0:
                self.byomi_time -= used
            else:
                self.byomi_time = self.byomi_time_org
            _next = self.byomi_time

        if start_timer:
            assert not self.timer or self.timer.finished.is_set(), "T " + str(self.timer)
            self.timer = GameClock(_next, self.overtime)
        return _next

    def __str__(self):
        return "{maintime}:{byomi_num}x{byomi_time}".format(**vars(self))

