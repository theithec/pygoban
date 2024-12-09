import pytest

from pygoban.receivers import BaseReceiver
from pygoban.results import ActionResult


class TestReceiver(BaseReceiver):
    def received_stone(self, result: ActionResult) -> None:
        pass

    def received_reset(self, result: ActionResult) -> None:
        pass

    def received_resign(self, result: ActionResult) -> None:
        pass

    def received_annotated(self, result: ActionResult) -> None:
        pass

    def received_count(self, result: ActionResult) -> None:
        pass

    def received_count_done(self, result: ActionResult) -> None:
        pass


@pytest.fixture
def receiver_cls():
    return TestReceiver
