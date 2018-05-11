import time
from threading import Thread
import subprocess

from . import STATUS, BLACK, WHITE


class Player():
    def __init__(self, col_id, name=None, game=None):
        self.col_id = col_id
        self.name = name or STATUS[col_id]

    def set_game(self, game):
        self._game = game

    def play(self, x, y):
        self._game.play(self.col_id, x, y)

    def set_turn(self, has_turn, result):
        pass


class ConsolePlayer(Player):
    def set_turn(self, has_turn, result):
        if has_turn:
            x = None
            while x is None:
                print("Player", STATUS[self.col_id])
                try:
                    txt = input(" x y: ")
                    x, y = [int(part) for part in txt.strip().split(" ")]
                except ValueError:
                    pass

            self.play(x, y)


def worker(cmd, player):
    player.process.stdin.write(("%s\r\n" % cmd).encode())
    player.process.stdin.flush()
    res = ""
    while True:
        nextline = player.process.stdout.readline().decode()
        if not nextline.strip():
            #  == '' and process.poll() is not None:
            break
        res += nextline

    player.handle_result(cmd, res)


class ThreadPlayer(Player):
    def __init__(self, *args, **kwargs):
        self.command = kwargs.pop('cmd')
        self.process = subprocess.Popen(
            self.command.split(" "),
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        super().__init__(*args, **kwargs)
        self.do_cmd("boardsize 9")
        self.do_cmd("showboard")

    def do_cmd(self, cmd):
        print("CMD", cmd)
        self.thread = Thread(target=worker, args=(cmd, self))
        self.thread.start()
        self.thread.join()

    def handle_result(self, cmd, res):
        if cmd.startswith("genmove"):
            coords = res.split("=")[-1].strip()
            self.play(*self._game.array_indexes(coords))

    def set_turn(self, has_turn, result):
        if has_turn:
            if result:
                coords = self._game.sgf_coords(result.x, result.y)
                self.do_cmd("play %s %s" % (
                    ("white" if self.col_id==BLACK else "black"),
                    coords))

            self.do_cmd("genmove %s" % ("white" if self.col_id==WHITE else "black"))
            self.do_cmd("showboard")
