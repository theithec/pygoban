import pytest

from pygoban.receivers import BaseReceiver
from pygoban import results


class TestReceiver(BaseReceiver):
    def __init__(self) -> None:  # type: ignore
        super().__init__()
        self.events = set([results.TurnDone])

    def received_turn(self, result: results.TurnDone) -> None:
        pass


@pytest.fixture
def receiver():
    return TestReceiver()
