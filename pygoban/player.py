import subprocess
import time
from threading import Thread

from . import logging, status, InputMode
from .coords import gtp_coords, array_indexes
from .events import MovePlayed, Counted


class Player:
    def __init__(self, color: status.Status, name=None):
        self.color = color
        self.name = name or str(color)
        self.timesettings = None
        self.controller = None

    def lost_by_overtime(self):
        self.end()
        self.controller.player_lost_by_overtime(self)

    def set_controller(self, controller):
        self.controller = controller

    def end(self):
        if self.timesettings and self.timesettings.timer:
            self.timesettings.timer.cancel()

    def set_timesettings(self, timesettings):
        self.timesettings = timesettings

    def _get_move(self):
        raise NotImplementedError()

    def set_turn(self, result):
        raise NotImplementedError()

    def __str__(self):
        return f"{self.color}"


class ConsolePlayer(Player):
    def _get_move(self):
        move = input(f"cmd {self.color}: ").strip()
        try:
            valid = True  # move in ("resign", "undo", "pass") or self._game.array_indexes(move)
            if move.startswith("#"):
                valid = False
        except (ValueError, IndexError):
            valid = False
        if not valid:
            return self._get_move()

        return move

    def handle_game_event(self, event):
        if isinstance(event, MovePlayed):
            if event.result.next_player == self.color:
                self.set_turn(event.result)

    def set_turn(self, result):
        try:
            move = self._get_move()
            self.controller.handle_gtp_move(self.color, move)
        except AssertionError:
            self.set_turn(result)


class GTPComm(Thread):
    def __init__(self, player, cmd, handle_output):
        super().__init__()
        self.player = player
        self.cmd = cmd
        self.handle_output = handle_output
        self.start()

    def run(self):
        if not self.player.process.pid:
            return

        time.sleep(0.3)

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
            logging.error("INAVLID(%s) %s -> %s", self.player, self.cmd, res)
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

    def set_controller(self, controller):
        super().set_controller(controller)
        self.process = subprocess.Popen(
            self.command.split(" "),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(1)
        self.do_cmd("boardsize %s" % self.controller.infos["SZ"], False)
        if (handicap := int(self.controller.infos.get("HA", 0))) > 0:
            self.do_cmd(f"fixed_handicap {handicap}", False)

    def set_timesettings(self, timesettings):
        self.timesettings = timesettings
        ts = self.timesettings
        self.do_cmd(
            f"time_settings {ts.maintime} {ts.byomi_time} {ts.byomi_stones}", False
        )

    def do_cmd(self, cmd, handle_output=True):
        GTPComm(self, cmd, handle_output=handle_output).join()

    def end(self):
        self.do_cmd("quit", False)
        self.process.wait()
        super().end()

    def _get_move(self):
        self.do_cmd("genmove " + self.color.strval.lower())

    def handle_game_event(self, event):
        result = event.result
        if isinstance(event, MovePlayed):
            if not event.result.exception:
                if result.move and result.move.pos and result.move.color != self.color:
                    coords = gtp_coords(*result.move.pos, self.controller.infos["SZ"])
                    self.do_cmd(
                        "play %s %s" % (result.move.color.strval.lower(), coords), False
                    )
                    self.do_cmd("showboard", False)
            if (
                self.controller.input_mode == InputMode.PLAY
                and result.next_player == self.color
            ):
                self._get_move()
