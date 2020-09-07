from lib.status import BLACK
from lib.player import Player
from lib.timesettings import TimeSettings, PlayerTime


def test_ts1():
    tst = PlayerTime(Player(BLACK), TimeSettings(maintime=60, byomi_time=30, byomi_num=3))
    assert tst.nexttime() == 60
    assert tst.nexttime(25) == 35
    assert tst.byomi_num == 3
    tst.overtime()
    assert tst.maintime == 0
    assert tst.byomi_num == 3
    assert tst.nexttime() == 30
    assert tst.nexttime(20) == 30
    assert tst.byomi_num == 3
    tst.overtime()
    assert tst.byomi_num == 2
    assert tst.nexttime(20) == 30
    assert tst.byomi_num == 2
    tst.overtime()
    assert tst.byomi_num == 1
    tst.cancel()
