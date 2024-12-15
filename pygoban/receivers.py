from abc import ABC, abstractmethod

from . import results


class BaseReceiver(ABC):  # ABC later

    def __init__(self) -> None:  # type: ignore
        self.last_turn: results.TurnDone | None = None

    @abstractmethod
    def received_turn(self, result: results.TurnDone) -> None: ...

    # @abstractmethod
    # def received_resign(self, result: ActionResult) -> None: ...

    @abstractmethod
    def received_annotated(self, result) -> None: ...

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
                self.last_turn = result
                self.received_turn(result)
            case results.AnnotationDone:
                self.received_annotated(result)
            case results.Counted:
                self.received_count(result)
            case results.TimeDone:
                self.received_period_ended(result)
            case results.GameResultDone:
                self.received_result_done(result)
            case _:
                pass
            # case AnnotatedDone:
            #    self.received_annotated(result)
        # self.curr_action_result = result
        # if result.stone_result:
        #    self.curr_stone_result = result.stone_result
        # print("received", result)
        # func = getattr(self, "received_" + str(result.type.name).lower())
        # func(result)
