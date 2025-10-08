from typing import Type, cast

from . import results


class BaseReceiver:
    def __init__(self) -> None:  # type: ignore
        self.last_turn: results.TurnDone | None = None
        self.events: set[Type[results.Event]] = set()

    def received_turn(self, result: results.TurnDone) -> None:
        raise NotImplementedError()

    def received_annotated(self, result: results.AnnotationDone) -> None:
        raise NotImplementedError()

    def received_count(self, result: results.Counted) -> None:
        raise NotImplementedError()

    def received_period_ended(self, result: results.TimeDone) -> None:
        raise NotImplementedError()

    def received_result_done(self, result: results.GameResultDone) -> None:
        raise NotImplementedError()

    def received_gtp_started(self, result: results.GTPStarted) -> None:
        raise NotImplementedError()

    def received_gtp_stopped(self, result: results.GTPStopped) -> None:
        raise NotImplementedError()

    def receive_game_event(self, result: results.Event) -> None:
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
            case results.GTPStarted:
                self.received_gtp_started(cast(results.GTPStarted, result))
            case results.GTPStopped:
                self.received_gtp_stopped(cast(results.GTPStarted, result))
