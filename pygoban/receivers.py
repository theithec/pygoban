from abc import ABC, abstractmethod
from typing import cast
from . import results


class BaseReceiver(ABC):

    def __init__(self) -> None:  # type: ignore
        self.last_turn: results.TurnDone | None = None

    @abstractmethod
    def received_turn(self, result: results.TurnDone) -> None: ...

    # @abstractmethod
    # def received_resign(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_annotated(self, result: results.AnnotationDone) -> None: ...

    @abstractmethod
    def received_count(self, result: results.Counted) -> None: ...

    # @abstractmethod
    # def received_count_done(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_period_ended(self, result: results.TimeDone) -> None: ...

    @abstractmethod
    def received_result_done(self, result: results.GameResultDone) -> None: ...

    # @abstractmethod
    # def received_lost_by_time(self, result: ActionResult) -> None: ...

    def receive_game_event(self, result: results.Event) -> None:
        print("Recevived", result)
        match result.__class__:
            case results.TurnDone:
                result = cast(results.TurnDone, result)
                self.last_turn = result
                self.received_turn(result)
            case results.AnnotationDone:
                self.received_annotated(cast(results.AnnotationDone, result))
            case results.Counted:
                self.received_count(cast(results.Counted, result))
            case results.TimeDone:
                self.received_period_ended(cast(results.TimeDone, result))
            case results.GameResultDone:
                self.received_result_done(cast(results.GameResultDone, result))
