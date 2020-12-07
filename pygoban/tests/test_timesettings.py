from unittest.mock import Mock
from pygoban.status import BLACK
from pygoban.player import Player
from pygoban.controller import Controller
from pygoban.timesettings import TimeSettings, PlayerTime


def test_ts1():
    player = Player(BLACK)
    player.controller = Mock()
    tst = PlayerTime(player, TimeSettings(maintime=60, byomi_time=30, byomi_num=3))
    assert tst.nexttime() == 60
    assert tst.nexttime(25) == 35
    assert tst.byomi.left == 3
    tst.period_ended()
    assert tst.maintime == 0
    assert tst.byomi.left == 3
    assert tst.nexttime() == 30
    assert tst.nexttime(20) == 30
    assert tst.byomi.left == 3
    tst.period_ended()
    assert tst.byomi.left == 2
    assert tst.nexttime(20) == 30
    assert tst.byomi.left == 2
    tst.period_ended()
    assert tst.byomi.left == 1
    tst.cancel()
