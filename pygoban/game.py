from enum import Enum
from threading import Timer
from typing import Dict, Tuple

from .board import Board, StonelessReason, MoveResult
from .move import Move
from .rulesets import BaseRuleset
from .status import BLACK, WHITE, Status
from .events import MovePlayed, CursorChanged, MovesReseted
from .sgf import INFO_KEYS


class End(Enum):
    RESIGN = "resign"
    BY_TIME = "by time"
    PASSED = "passed"


class ThreeTimesPassed(Exception):
    pass


HANDICAPS: Dict[int, Tuple] = {1: ((15, 3),)}
HANDICAPS[2] = HANDICAPS[1] + ((3, 15),)


class Game:
    def __init__(self, **infos):
        self.infos = {k: v for k in INFO_KEYS if (v := infos.get(k))}
        self.board = Board(int(infos["SZ"]))
        self.ruleset = BaseRuleset(self)
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.root = Move(color=None, pos=None)
        self._cursor = self.root
        self.registrations = {}

    @property
    def boardsize(self):
        return self.board.boardsize

    @property
    def cursor(self):
        return self._cursor

    def get_othercolor(self, color: Status):
        assert color in (BLACK, WHITE, None)
        return BLACK if not color or color == WHITE else WHITE

    @property
    def nextcolor(self):
        return self.get_othercolor(self.cursor.color)

    def play(self, color: Status, pos):
        move = Move(color, pos)
        result = self._test_move(move)
        self.ruleset.validate(result)
        self._apply_result(result)
        self.fire_event(CursorChanged(result, self.board))
        self.fire_event(MovePlayed(result))

    def start(self):
        print("START")
        self._set_cursor(self.cursor)
        result = MoveResult(
            next_player=self.nextcolor,
            move=self.cursor,
            extra=StonelessReason.FIRST_MOVE if self.cursor.is_root else None,
            is_new=self.cursor.is_root,
        )
        self.fire_event(MovesReseted(self.root))
        self.fire_event(MovePlayed(result))

    def add_listener(self, instance, event_classes=None):
        event_classes = event_classes or [MovePlayed]
        for event_class in event_classes:
            self.registrations.setdefault(event_class, [])
            self.registrations[event_class].append(instance)

    def fire_event(self, event):
        listeners = self.registrations.get(event.__class__, [])
        # print("FIRE", event, listeners)
        for listener in listeners:
            _timer = Timer(0, lambda: listener.handle_game_event(event))
            _timer.start()

    def pass_(self, color):
        if self.cursor.is_pass and self.cursor.parent and self.cursor.parent.is_pass:
            raise ThreeTimesPassed(color)
        self._test_move(Move(color, pos=None), apply_result=True)

    def undo(self):
        old_color = self.cursor.color
        parent = self.cursor.parent
        self._set_cursor(parent, no_fire=True)
        result = MovePlayed(
            MoveResult(
                next_player=old_color,
                move=Move(color=self.cursor.color),
                extra=StonelessReason.UNDO,
                is_new=False,
            )
        )
        self.fire_event(result)

    def _set_cursor(self, move, no_fire=False):
        self._cursor = move
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.board = Board(self.board.boardsize)
        self._set_handicap()
        path = self.get_path()
        self._cursor = self.root
        for pmove in path:
            self._test_move(pmove, apply_result=True)
        if not no_fire:
            self.fire_event(
                CursorChanged(
                    MoveResult(
                        next_player=self.nextcolor, move=self.cursor, is_new=False
                    ),
                    self.board,
                )
            )

    def _test_move(self, move, apply_result=False):
        is_new = True
        if child := self.cursor.children.get(move.pos):
            if child.color == move.color:
                move = child
                is_new = False

        if move.pos:
            result = self.board.result(move)
            result.is_new = is_new
        else:
            extra = StonelessReason.PASS if move.is_pass else StonelessReason.ADD_STONES
            result = MoveResult(
                next_player=self.get_othercolor(self.nextcolor),
                move=move,
                extra=extra,
                is_new=is_new,
            )

        result.move = move
        result.next_player = result.next_player or self.get_othercolor(self.nextcolor)
        if apply_result:
            self._apply_result(result)

        return result

    def to_sgf(self):
        boardsize = self.board.boardsize

        def add_children(move):
            nonlocal txt

            parent = move.parent
            is_variation = parent and parent.children and len(parent.children) > 1
            if is_variation:
                txt += "("
            txt += move.to_sgf(boardsize)

            for childlist in move.children.values():
                for child in childlist:
                    add_children(child)
            if is_variation:
                txt += ")"

        txt = "(;" + "".join([f"{k}[{v}]" for k, v in self.infos.items()])
        txt += self.root.to_sgf(boardsize)
        add_children(self.root)
        txt += ")"
        return txt

    def _set_handicap(self):
        handicap = self.infos.get("HA")
        if not handicap:
            return
        positions = HANDICAPS.get(handicap, tuple())
        for pos in positions:
            self.board[pos[0]][pos[1]] = BLACK

    def _apply_result(self, result):
        if result.move.pos and result.move.color:
            self.board.apply_result(result)
            self.prisoners[result.move.color] += len(result.killed)
        elif result.move.extras.has_stones():
            for status in (BLACK, WHITE):
                poss = result.move.extras.stones[status]
                for pos in poss:
                    x, y = pos
                    self.board[x][y] = status

        if not result.move.parent:
            result.move.parent = self.cursor
        self._cursor = result.move

        # self.fire_event(CursorChanged(result, self.board))
        # self.fire_event(MovePlayed(result))

    def get_path(self):
        return self.cursor.get_path()

    def tree(self, curr=None, level=1):
        print("\t" * level, curr, " Parent: ", curr.parent if curr else "-")
        curr = curr or self.root
        children = curr.children
        if children:
            level += 1
            for innerchildren in children.values():
                for child in innerchildren:
                    self.tree(child, level)
