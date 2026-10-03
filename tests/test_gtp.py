from threading import Event

from pygoban import Color, Game, GameInfo, gtp
from pygoban.rulesets.japanese import JapaneseRuleset


class FakeStdin:
    def __init__(self):
        self.commands: list[str] = []

    def write(self, value: bytes) -> int:
        self.commands.append(value.decode().strip())
        return len(value)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class FakeStdout:
    def __init__(self, lines=()):
        self.lines = list(lines)
        self.ready = Event()

    def readline(self) -> bytes:
        if self.lines:
            return self.lines.pop(0)
        self.ready.wait()
        return b""

    def close(self) -> None:
        self.ready.set()


class FakeProcess:
    pid = 1

    def __init__(self, lines=()):
        self.stdin = FakeStdin()
        self.stdout = FakeStdout(lines)
        self.returncode: int | None = None

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = 0
        self.stdout.ready.set()
        return self.returncode

    def kill(self) -> None:
        self.returncode = -9
        self.stdout.ready.set()


def make_game() -> Game:
    ruleset = JapaneseRuleset(
        boardsize=9,
        komi=0.5,
        handicap=0,
        info=GameInfo(names={Color.BLACK: "Black", Color.WHITE: "White"}),
    )
    return Game(ruleset)


def test_full_analysis_can_restart_stopped_process(monkeypatch):
    processes = []

    def start_process(_command):
        process = FakeProcess()
        processes.append(process)
        return process

    monkeypatch.setattr(gtp, "get_process", start_process)
    controller = gtp.GTPController(name="engine", cmd_line="engine", game=make_game())

    assert controller.toggle_action(gtp.Role.ANALYZE_FULL)
    first_process = controller.process
    assert first_process is processes[0]

    assert not controller.toggle_action(gtp.Role.ANALYZE_FULL)
    assert controller.process is None
    assert first_process.stdin.commands == ["stop", "quit"]

    assert controller.toggle_action(gtp.Role.ANALYZE_FULL)
    assert controller.process is processes[1]
    assert controller.process is not first_process

    controller.quit()


def test_stopping_full_analysis_keeps_process_for_other_roles(monkeypatch):
    processes = []

    def start_process(_command):
        process = FakeProcess()
        processes.append(process)
        return process

    monkeypatch.setattr(gtp, "get_process", start_process)
    controller = gtp.GTPController(name="engine", cmd_line="engine", game=make_game())
    controller.toggle_action(gtp.Role.ANALYZE)
    controller.toggle_action(gtp.Role.ANALYZE_FULL)
    process = controller.process

    controller.toggle_action(gtp.Role.ANALYZE_FULL)

    assert controller.process is process
    assert process.stdin.commands == ["stop"]
    assert len(processes) == 1

    controller.quit()


def test_reader_continues_after_gtp_blank_line(monkeypatch):
    controller = gtp.GTPController(name="engine", cmd_line="engine", game=make_game())
    process = FakeProcess([b"= ready\n", b"\n", b"info analysis\n"])
    process.stdout.ready.set()
    controller.process = process
    controller.is_running = True
    controller.annotate_res = lambda _result: setattr(controller, "saw_analysis", True)

    controller.loop(process)

    assert controller.saw_analysis
    assert not controller.is_running


def test_quit_stops_analysis_before_exiting_engine(monkeypatch):
    processes = []

    def start_process(_command):
        process = FakeProcess()
        processes.append(process)
        return process

    monkeypatch.setattr(gtp, "get_process", start_process)
    controller = gtp.GTPController(name="engine", cmd_line="engine", game=make_game())
    controller.toggle_action(gtp.Role.ANALYZE_FULL)
    process = controller.process

    controller.quit()

    assert process.stdin.commands == ["stop", "quit"]
    assert controller.process is None


def test_analysis_marks_order_zero_as_best_move():
    controller = gtp.GTPController(name="engine", cmd_line="engine", game=make_game())
    results = {}
    controller.annotate_winrates = lambda infos, best_move=None: results.update(
        infos=infos, best_move=best_move
    )
    output = (
        "info move D4 visits 10 edgeVisits 10 utility -0.1 winrate 0.55 "
        "scoreMean 2 scoreStdev 1 scoreLead 2 scoreSelfplay 2 prior 0.4 "
        "lcb 0.5 utilityLcb -0.2 weight 1 order 3 pv D4 C3 "
        "info move Q4 visits 8 edgeVisits 8 utility 0.1 winrate 0.45 "
        "scoreMean -1 scoreStdev 1 scoreLead -1 scoreSelfplay -1 prior 0.3 "
        "lcb 0.4 utilityLcb -0.3 weight 1 order 0 pv Q4 C3"
    )

    controller.annotate_res(output)

    assert results["best_move"] == gtp.gtp_coord_to_pos("Q4", 9)
    assert results["infos"][results["best_move"]][3] == 0
