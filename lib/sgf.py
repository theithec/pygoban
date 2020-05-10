import re
from . import logging
from .status import BLACK, WHITE
from .movetree import MoveTree


class Parser:
    def __init__(self, sgftxt):
        self.txt = sgftxt
        #self.info_pattern = re.compile(r"([A-Z]{2})\[(.*?)[^\\]\](.*)")
        self.info_pattern = re.compile(r"([A-Z]{1,2})\[(.*?)\](?<!\\)(.*)$", re.DOTALL)

        self.move_pattern = re.compile(r"([A-Z]{1,2})\[(.*?)\](?<!\\)(.*)", re.MULTILINE)
        self.variations = []
        self.infos = {}
        self.tree = None

    def _parse_intro(self, intro):
        while intro := intro.strip():
            print("i", intro)
            key, val, rest = self.info_pattern.search(intro).groups()
            print("kv1", key, val) #, rest)
            self.infos[key] = val
            intro = rest
        self.tree = MoveTree(**self.infos)

    def _parse_moves(self, moves):
        moves = moves.split(";")
        for move in moves:
            move = move.strip()
            try:
                key, val, rest = self.move_pattern.match(move).groups()
            except AttributeError:
                print("m", move)
            print(key, val, rest)

    def _parse_moves2(self, moves):
        moves = moves.split(";")
        for move in moves:
            fullmove = move.rstrip()
            move_end = move.find("]")
            move = fullmove[:move_end + 1]
            print("m", move)

            colchar, ychar, xchar = self.move_pattern.match(move).groups()
            color = BLACK if colchar == "B" else WHITE
            x = 96 - ord(xchar) + int(self.infos["SZ"])
            y = ord(ychar) - 97
            self.tree.test_move(color, x, y, apply_result=True)
            print(self.tree.board)
            while True:
                move_end += 1
                try:
                    char = fullmove[move_end]
                except IndexError:
                    break
                if char == "(":
                    self.variations.append(self.tree.cursor)
                elif char == ")":
                    self.tree.set_cursor(self.variations.pop())

    def _parse(self, txt):
        _, intro, moves = txt.split(";", 2)
        self._parse_intro(intro)
        self._parse_moves(moves)

    def parse(self):
        self._parse(self.txt.strip()[1:-1])

