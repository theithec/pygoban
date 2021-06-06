from __future__ import annotations

import subprocess
import time
from threading import Thread
from typing import TYPE_CHECKING, Optional, List

from . import InputMode, logging, status
from .coords import array_indexes, gtp_coords
from .events import CursorChanged, Undo
from .move import Empty, Move

if TYPE_CHECKING:
    from pygoban.timesettings import TimeSettings
    from pygoban.controller import Controller


class Player:
    def __init__(self, color: status.Status, name=None):
        self.color = color
        self.name = name or str(color)
        self.clock: Optional[TimeSettings] = None
        self.controller: Optional[Controller] = None
        self.moves: List[Move] = []

    def set_controller(self, controller):
        self.controller = controller

    def end(self):
        if self.clock and self.clock.timer:
            self.clock.timer.cancel()

    def handle_game_event(self, event):

        logging.info("Handle game event (%s), input_mode=%s, event=%s", self, self.controller.input_mode, event)
        if isinstance(event, CursorChanged) and event.next_player == self.color:
            move = self._get_move()
            if move:
                self.controller._play(self.color, move.pos)
                return True
        return False

    def _get_move(self):
        if self.moves:
            return self.moves.pop(0)
        return None

    def set_clock(self, clock):
        self.clock = clock

    def __str__(self):
        return f"{self.color}({self.name})"

class PassingPlayer(Player):
    passed = False
    def _get_move(self):
        print("GET MOVE")
        move = super()._get_move()
        if not move and not self.passed:
            self.passed = True
            move = Move(color=self.color, pos=Empty.PASS)
        return move

class ConsolePlayer(Player):
    def _get_move(self):
        move = super()._get_move() or input(f"cmd {self.color}: ").strip()
        try:
            valid = move.lower() in ("resign", "undo", "pass") or array_indexes(move, self.controller.infos["SZ"])
            if move.startswith("#"):
                valid = False
        except (ValueError, IndexError):
            valid = False
        if not valid:
            return self._get_move()

        return move


class GTPComm(Thread):
    def __init__(self, player, cmd, handle_output):
        super().__init__()
        self.player = player
        self.cmd = cmd
        self.handle_output = handle_output
        self.start()

    def run(self):

        logging.debug("gtpcmd0(%s) %ss", self.player, self.cmd)
        if not self.player.process.pid:
            return

        # time.sleep(0.3)

        try:
            self.player.process.stdin.write(("%s\r\n" % self.cmd).encode())
            self.player.process.stdin.flush()
        except BrokenPipeError:
            return
        res = ""
        while self.player.process.pid:
            try:
                nextline = self.player.process.stdout.readline().decode()
                if not nextline.strip():
                    break
            except BrokenPipeError:
                break
            res += nextline

        logging.info("gtpcmd(%s) %s -> %s", self.player, self.cmd, res)
        if res.strip().startswith("?"):
            logging.error("INVALID(%s) %s -> %s", self.player, self.cmd, res)
            self.player.controller.end("Exception {color}", self.player.color)
        if self.handle_output:
            res = res.lower()
            move = res.split("=")[-1].strip()
            if move:
                self.player.controller.handle_gtp_move(self.player.color, move)


class GTPPlayer(Player):
    def __init__(self, *args, **kwargs):
        self.command = kwargs.pop("cmd")
        super().__init__(*args, **kwargs)
        self.process = None

    def set_controller(self, controller):
        super().set_controller(controller)
        self.process = subprocess.Popen(
            self.command.split(" "),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        # time.sleep(1)
        self.do_cmd("boardsize %s" % self.controller.infos["SZ"], False)
        if (handicap := int(self.controller.infos.get("HA", 0))) > 0:
            self.do_cmd(f"fixed_handicap {handicap}", False)

    def set_clock(self, clock):
        self.clock = clock
        self.do_cmd(
            cmd=f"clock {clock.maintime} {clock.byoyomi_time} {clock.byoyomi_stones}",
            handle_output=False,
        )

    def do_cmd(self, cmd, handle_output=True):
        GTPComm(self, cmd, handle_output=handle_output).join()
        GTPComm(self, "showboard", handle_output=False).join()

    def end(self):
        self.do_cmd("quit", False)
        self.process.wait()
        super().end()

    def _get_move(self):
        move = super()._get_move()
        if move:
            logging.debug("Found move (%s) %s", self, move)
            vertex = gtp_coords(*move.pos, self.controller.infos["SZ"])
            self.do_cmd("play %s %s" % (self.color.strval.lower(), vertex))
            self.controller._play(self.color, move.pos)
        else:
            self.do_cmd("genmove " + self.color.strval.lower())

    def handle_game_event(self, event):
        if event.exception:
            return
        vertex = None
        logging.info("Handle game event (%s), input_mode=%s, event=%s", self, self.controller.input_mode, event)

        if isinstance(event, Undo) and event.next_player == self.color:
            self.do_cmd("undo")
            self.do_cmd("undo")
            self.controller.handle_gtp_move(self.color, "undo")
            return
        elif isinstance(event, CursorChanged) and (
            event.next_player == self.color
        ):
            logging.debug("E22 %s", event)
            if event.cursor.is_pass:
                vertex = "pass"
            # elif event.cursor.is_empty:
            #    print("C", event.cursor)
            #    pass
            #    vertex = "pass"
            #    #    print("C", result.cursor)
            # self.do_cmd("undo")
            # self.controller.handle_gtp_move(self.color, "pass")
            elif not isinstance(event.cursor.pos, Empty):
                vertex = gtp_coords(*event.cursor.pos, self.controller.infos["SZ"])
            if vertex:
                self.do_cmd("play %s %s" % (event.cursor.color.strval.lower(), vertex), False)
                # self.do_cmd("showboard", False)
            #if self.controller.input_mode == InputMode.PLAY:
            if event.next_player == self.color:
                self._get_move()
