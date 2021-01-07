from unittest.mock import Mock
from pygoban.status import BLACK
from pygoban.player import Player
from pygoban.controller import Controller
from pygoban.timesettings import TimeSettings, PlayerTime


def test_ts1():
    player = Player(BLACK)
    player.controller = Mock()
    tst = PlayerTime(player, TimeSettings(maintime=60, byoyomi_time=30, byoyomi_num=3))
    assert tst.nexttime() == 60
    tst.subtract(25)
    assert tst.nexttime() == 35
    assert tst.byoyomi.periods_left == 3
    tst.period_ended()
    assert tst.maintime == 0
    assert tst.byoyomi.periods_left == 3
    assert tst.nexttime() == 30
    tst.subtract(20)
    assert tst.nexttime() == 30
    assert tst.byoyomi.periods_left == 3
    tst.period_ended()
    assert tst.byoyomi.periods_left == 2
    tst.subtract(20)
    assert tst.nexttime() == 30
    assert tst.byoyomi.periods_left == 2
    tst.period_ended()
    assert tst.byoyomi.periods_left == 1
    tst.cancel_timer()
