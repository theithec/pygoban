import pytest

from pygoban.receivers import BaseReceiver
from pygoban.results import ActionResult


class TestReceiver(BaseReceiver):
    def do_stone(self, result: ActionResult) -> None:
        pass

    def do_reset(self, result: ActionResult) -> None:
        pass

    def do_resign(self, result: ActionResult) -> None:
        pass

    def do_annotated(self, result: ActionResult) -> None:
        pass

    def do_count(self, result: ActionResult) -> None:
        pass

    def do_count_done(self, result: ActionResult) -> None:
        pass


@pytest.fixture
def receiver_cls():
    return TestReceiver
