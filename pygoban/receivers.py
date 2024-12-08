from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .results import ActionResult, ActionType
from .rulesets import Ruleset
from .stone import Stone

if TYPE_CHECKING:
    from .game import AbstractCallbacks
    from .gamecontroller import GameController


class BaseReceiver:
    curr_action_result: ActionResult | None
    curr_stone: Stone

    def __init__(
        self,
        # controller: "GameController",
        # ruleset: Ruleset,
    ) -> None:  # type: ignore
        #  #     self.ruleset = ruleset
        self.curr_action_result = None
        # self.controller: GameController = controller

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

    def receive_game_event(self, result: ActionResult):
        self.curr_action_result = result
        print("received", self.curr_action_result)
        if result.stone_result:
            self.curr_stone = result.stone_result.stone
        func = getattr(self, "received_" + str(result.type.name).lower())
        func(result)
