from . import logging
from typing import Type
import time
import datetime
from threading import Thread
import subprocess
from . import status


class Player():
    def __init__(self, color: Type["status.Status"], name=None):
        self.color = color
        self.name = name or str(color)

    def lost_by_overtime(self):
        self.end()
        self.controller.player_lost_by_overtime(self)

    def set_controller(self, controller):
        self.controller = controller

    def end(self):
        pass

    def set_timesettings(self, timesettings):
        self.timesettings = timesettings

    def _get_move(self):
        raise NotImplementedError()

    def set_turn(self, result):
        raise NotImplementedError()


class ConsolePlayer(Player):
    def _get_move(self):
        move = input("cmd: ").strip()
        try:
            valid = True  # move in ("resign", "undo", "pass") or self._game.array_indexes(move)
            if move.startswith("#"):
                valid = False
        except (ValueError, IndexError):
            valid = False
        if not valid:
            return self._get_move()

        return move

    def set_turn(self, result):
        try:
            move = self._get_move()
            self.controller.handle_move(self.color, move)
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

        logging.info("gtpcmd %s -> %s", self.cmd, res)
        if self.handle_output:
            res = res.lower()
            move = res.split("=")[-1].strip()
            if move:
                self.player.controller.handle_move(self.player.color, move)


class GTPPlayer(Player):
    def __init__(self, *args, **kwargs):
        self.command = kwargs.pop('cmd')
        super().__init__(*args, **kwargs)

    def set_controller(self, controller):
        super().set_controller(controller)
        self.process = subprocess.Popen(
            self.command.split(" "),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        time.sleep(1)
        self.do_cmd("boardsize %s" % self.controller.game.movetree.board.boardsize, False)

    def set_timesettings(self, timesettings):
        self.timesettings = timesettings
        ts = self.timesettings
        self.do_cmd(f"time_settings {ts.maintime} {ts.byomi_time} {ts.byomi_stones}", False)

    def do_cmd(self, cmd, handle_output=True):
        GTPComm(self, cmd, handle_output=handle_output).join()

    def end(self):
        self.do_cmd("quit", False)
        self.process.wait()

    def _get_move(self):
        # self.controller.handle_move(self.color, "pass")
        self.do_cmd("genmove " + self.color.strval.lower())

    def set_turn(self, result):
        if result:
            if not result.extra:
                coords = self.controller.game.sgf_coords(result.x, result.y)
                self.do_cmd("play %s %s" % (
                    result.color.strval.lower(),
                    coords), False)
                self.do_cmd("showboard", False)
        self._get_move()
