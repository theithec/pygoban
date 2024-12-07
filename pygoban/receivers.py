from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .results import ActionResult, ActionType
from .rulesets import Ruleset

if TYPE_CHECKING:
    from .game import AbstractCallbacks


class BaseReceiver(ABC):
    curr_action_result: ActionResult | None

    def __init__(
        self,
        # ruleset: Ruleset,
    ) -> None:  # type: ignore
        #  #     self.ruleset = ruleset
        self.curr_action_result = None

    @abstractmethod
    def do_stone(self, result: ActionResult) -> None: ...

    @abstractmethod
    def do_reset(self, result: ActionResult) -> None: ...

    @abstractmethod
    def do_resign(self, result: ActionResult) -> None: ...

    @abstractmethod
    def do_annotated(self, result: ActionResult) -> None: ...

    @abstractmethod
    def do_count(self, result: ActionResult) -> None: ...

    @abstractmethod
    def do_count_done(self, result: ActionResult) -> None: ...

    def receive_game_event(self, result: ActionResult):
        self.curr_action_result = result
        func = getattr(self, f"do_{str(result.type.name).lower()}")
        func(result)

    def set_action(self, action, status):
        pass
