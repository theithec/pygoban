import time
from pygoban import Game, Ruleset, results, GameInfo
from pygoban.receivers import BaseReceiver
from pygoban.timesettings import TimeSettings


class Receiver(BaseReceiver):
    def __init__(self):
        super().__init__()
        self.events = set([results.TimeDone, results.GameResultDone])


def test_timesettings(mocker):
    receiver = Receiver()
    mocked_received_period_ended = mocker.patch.object(
        receiver, "received_period_ended"
    )
    mocked_received_game_result = mocker.patch.object(receiver, "received_result_done")
    ruleset = Ruleset(
        boardsize=5,
        komi=0,
        handicap=0,
        timesettings=TimeSettings(maintime=1, byoyomi_time=1, byoyomi_num=1),
        info=GameInfo(),
    )
    game = Game(ruleset=ruleset)
    game.start(receivers=[receiver])
    time.sleep(2.1)
    assert mocked_received_period_ended.call_count == 2
    mocked_received_game_result.assert_called_once()
