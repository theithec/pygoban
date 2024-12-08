from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .results import ActionResult, ActionType, StoneResult
from .rulesets import Ruleset
from .stone import Stone

if TYPE_CHECKING:
    from .game import AbstractCallbacks
    from .gamecontroller import GameController


class BaseReceiver:  # ABC later
    curr_action_result: ActionResult | None
    curr_stone_result: StoneResult

    def __init__(self) -> None:  # type: ignore
        self.curr_action_result = None

    @abstractmethod
    def received_stone(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_reset(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_resign(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_annotated(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_count(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_count_done(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_period_ended(self, result: ActionResult) -> None: ...

    def receive_game_event(self, result: ActionResult):
        self.curr_action_result = result
        if result.stone_result:
            self.curr_stone_result = result.stone_result
        func = getattr(self, "received_" + str(result.type.name).lower())
        print("CALL", func)
        func(result)
