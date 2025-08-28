import logging
import os
import re
import subprocess
import threading
from collections.abc import Iterable
from typing import cast

from . import results
from .coords import gtp_coord_to_pos, pos_to_gtp_coord
from .game import Game
from .gamecontroller import SubGameController
from .receivers import BaseReceiver

# example analyses output
# move C4 visits 11782 edgeVisits 11783 utility 0.800618 winrate 0.906799 scoreMean 1.4196
# scoreStdev 6.7351 scoreLead 1.4196 scoreSelfplay 2.13197 prior 0.117485 lcb 0.903819
# utilityLcb 0.792274 weight 12337 order 0 pv C4 D3 C6 D6 C7 C3 G4 D7 F5 H5 G6 E4 B3 B2

KATA_ANALYZE_STR = (
    r"move (\S+) visits (\S+?) edgeVisits \S+? utility (\S+?) winrate (\S+?) scoreMean (\S+?) "
    r"scoreStdev (\S+?) scoreLead (\S+?) scoreSelfplay (\S+?) prior (\S+?) lcb (\S+?) "
    r"utilityLcb (\S+?) weight (\S+?) .*?order (\S+?) pv (.*)"
)

COORD_OR_PASS = r"= ([A-Z]\d{1,2}|PASS)"
pattern = re.compile((KATA_ANALYZE_STR))


class GTPException(Exception):
    pass


class GTPController(BaseReceiver, SubGameController):
    def __init__(self, cmd_line: str, game: Game, actions: Iterable[str] | None = None):
        BaseReceiver.__init__(self)
        SubGameController.__init__(self, game=game)
        self.autoplay = False
        self.receiver = self
        self.events = {results.TurnDone, results.GameResultDone, results.Counted}
        self.process = self.get_process(cmd_line)
        self.is_running = True
        self.actions: set[str] = set()
        if actions:
            for action in actions:
                self.set_action(action, True)
        logging.debug("START GTP LOOP %s", self)
        self.got_turn = False
        thread = threading.Thread(target=self.loop, args=tuple())
        thread.start()

    def loop(self):
        def parse_output() -> str:
            assert self.process.stdout
            nextline = self.process.stdout.readline().decode().strip()
            res = nextline + os.linesep
            if nextline.startswith("info "):
                self.annotate_res(res)
            elif nextline.startswith("= resign"):
                assert self.last_turn
                self.set_end_result(
                    results.GameResultType.RESIGN,
                    color=cast(results.TurnDone, self.last_turn).next_color,
                )
            if match := re.match(COORD_OR_PASS, nextline):
                val = match.group(1).strip()
                if val == "PASS":
                    pos = None
                else:
                    pos = gtp_coord_to_pos(val, self.ruleset.boardsize)
                assert self.last_turn
                self.play(self.last_turn.next_color, pos)
            elif part := nextline[0:50].strip():
                logging.debug("GTP OUT: %s", part)
            return res

        while self.is_running and self.process.pid:
            try:
                res = parse_output()
            except BrokenPipeError as err:
                logging.debug(err)
                break  # raise

            if res.startswith("?"):
                raise GTPException(f"{res}")
            if not self.is_running:
                break

    def get_process(self, cmd_line: str):
        return subprocess.Popen(
            cmd_line.split(" "),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def do_cmd(self, cmd: str):
        if not self.is_running:
            return
        print("do cmd", cmd)
        try:
            assert self.process.stdin
            self.process.stdin.write(f"{cmd}\r\n".encode())
            self.process.stdin.flush()
        except (BrokenPipeError, ValueError):
            logging.warning("Connection broke", exc_info=True)
            return

    def annotate_res(self, res):
        parts = res.split("info ")
        parts = parts[0: min(11, len(parts))]
        infos = {}
        for part in parts:
            if not part:
                continue
            match = pattern.search(part)
            if match:
                groups = match.groups()
                if (group0 := groups[0]) == "pass":
                    continue
                pos = gtp_coord_to_pos(group0, self.ruleset.boardsize)
                winrate = float(groups[3]) * 100
                score = float(groups[4])
                moves = [
                    None if coord == "pass" else gtp_coord_to_pos(coord, self.ruleset.boardsize)
                    # gtp_coord_to_pos(coord, self.ruleset.boardsize)
                    for coord in groups[13].strip().split()
                ]
                infos[pos] = (str(winrate)[0:4], str(score), moves)
        self.annotate_winrates(infos)
        if self.autoplay and self.last_stone:
            if self.last_stone.children:
                node = self.last_stone.children[-1]
                self.play(node.color, node.pos)
            else:
                self.set_action("analyze_full", False)
                self.do_cmd("stop")

    def set_action(self, action: str, status: bool):
        if action == "analyze_full":
            self.autoplay = status
            action = "analyze"
        if status:
            self.actions.add(action)
        elif action in self.actions:
            self.actions.remove(action)

    def received_turn(self, result: results.TurnDone) -> None:
        if result.reset:
            self.got_turn = False
            self.do_cmd(cmd="clear_board")
            self.do_cmd(f"boardsize {self.ruleset.boardsize}")
            komi = self.ruleset.komi
            if int(komi == 375):  # fox
                komi = 7.5
            self.do_cmd(f"komi {komi}")
            if self.ruleset.handicap:
                self.do_cmd(f"fixed_handicap {self.ruleset.handicap}")
                assert self.last_turn and self.last_turn.node
                for pos, color in self.last_turn.node.annos.stones.items():
                    coord = pos_to_gtp_coord(pos, self.ruleset.boardsize)
                    self.do_cmd(cmd=f"play {color.name} {coord}")

            for node in result.node.path():
                if node.pos:
                    coord = pos_to_gtp_coord(node.pos, boardsize=self.ruleset.boardsize)
                    self.do_cmd(cmd=f"play {node.color.name} {coord}")
        else:
            node = result.node
            if node.color not in self.actions:
                if node.pos:
                    coord = pos_to_gtp_coord(node.pos, boardsize=self.ruleset.boardsize)
                    self.do_cmd(cmd=f"play {node.color.name} {coord}")
        is_undo = result.reset and result.node.pos and self.got_turn
        if result.next_color in self.actions and not is_undo:
            self.do_cmd(f"genmove {result.next_color}")

        if "analyze" in self.actions:
            self.do_cmd(f"kata-analyze {result.next_color.name} 100")

        self.got_turn = True

    def quit(self):
        self.do_cmd("quit")
        self.is_running = False
        try:
            logging.debug("TRY KILL %s ", self)
            outs, errs = self.process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            logging.debug("TIMEOUT ON KILL %s", self)
            self.process.kill()
            outs, errs = self.process.communicate()
        logging.debug("KILLED %s - out: '%s', errs: '%s'", self, outs, errs)

    def received_annotated(self, result: results.AnnotationDone) -> None: ...

    def received_count(self, result: results.Counted) -> None:
        self.set_action("analyze_full", False)
        self.do_cmd("quit")

    def received_period_ended(self, result: results.TimeDone) -> None: ...

    def received_result_done(self, result: results.GameResultDone) -> None:
        self.do_cmd("stop")
