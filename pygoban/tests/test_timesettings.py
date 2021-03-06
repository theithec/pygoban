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
    assert tst.nexttime(25) == 35
    assert tst.byoyomi.left == 3
    tst.period_ended()
    assert tst.maintime == 0
    assert tst.byoyomi.left == 3
    assert tst.nexttime() == 30
    assert tst.nexttime(20) == 30
    assert tst.byoyomi.left == 3
    tst.period_ended()
    assert tst.byoyomi.left == 2
    assert tst.nexttime(20) == 30
    assert tst.byoyomi.left == 2
    tst.period_ended()
    assert tst.byoyomi.left == 1
    tst.cancel()
