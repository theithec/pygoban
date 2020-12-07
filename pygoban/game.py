from threading import Timer
from typing import Dict, Tuple

from .board import Board, StonelessReason, MoveResult
from .move import Move
from .rulesets import BaseRuleset, RuleViolation
from .status import BLACK, WHITE, Status
from .events import MovePlayed, CursorChanged, MovesReseted, Counted, Ended
from .counting import count
from .sgf import INFO_KEYS
from . import logging, GameResult, END_BY_RESIGN


HANDICAPS: Dict[int, Tuple] = {1: ((3, 3),)}
HANDICAPS[2] = (
    (3, 3),
    (15, 15),
)
HANDICAPS[3] = HANDICAPS[2] + ((15, 3),)
HANDICAPS[4] = HANDICAPS[3] + ((3, 15),)
HANDICAPS[5] = HANDICAPS[4] + ((9, 9),)
HANDICAPS[6] = HANDICAPS[4] + (
    (9, 3),
    (9, 15),
)
HANDICAPS[7] = HANDICAPS[6] + ((9, 9),)
HANDICAPS[8] = HANDICAPS[7] + ((3, 9),)
HANDICAPS[9] = HANDICAPS[8] + ((15, 9),)


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
        if not self.cursor.parent and int(self.infos.get("HA", 0)) > 1:
            return WHITE
        return self.get_othercolor(self.cursor.color)

    def play(self, color: Status, pos):
        move = Move(color, pos)
        result = self.test_move(move)
        try:
            self.ruleset.validate(result)
        except RuleViolation as err:
            # logging.info("RuleViolation: %s", err)
            result.exception = err
            result.next_player = color
        if not result.exception:
            self._apply_result(result)

        self.fire_event(CursorChanged(result, self.board))
        self.fire_event(MovePlayed(result))
        return result

    def start(self):
        self._set_cursor(self.cursor)
        result = MoveResult(
            next_player=self.nextcolor,
            move=self.cursor,
            extra=StonelessReason.FIRST_MOVE if self.cursor.is_root else None,
            is_new=self.cursor.is_root,
        )
        self.fire_event(MovesReseted(self.root))
        self.fire_event(MovePlayed(result))

    def _set_handicap(self):
        handicap = self.infos.get("HA")
        if not handicap:
            return
        positions = HANDICAPS.get(handicap, tuple())
        for pos in positions:
            self.board[pos[0]][pos[1]] = BLACK

    def add_listener(self, instance, event_classes=None):
        event_classes = event_classes or [MovePlayed]
        for event_class in event_classes:
            self.registrations.setdefault(event_class, [])
            self.registrations[event_class].append(instance)

    def fire_event(self, event):
        listeners = self.registrations.get(event.__class__, [])
        for listener in listeners:
            _timer = Timer(0, lambda: listener.handle_game_event(event))
            _timer.start()

    def pass_(self, color):
        if self.cursor.is_pass and self.cursor.parent and self.cursor.parent.is_pass:
            self.count()
        result = self.test_move(Move(color, pos=None), apply_result=True)
        self.fire_event(CursorChanged(result, self.board))
        self.fire_event(MovePlayed(result))

    def undo(self):
        old_color = self.cursor.color
        parent = self.cursor.parent
        self._set_cursor(parent)
        result = MovePlayed(
            MoveResult(
                next_player=old_color,
                move=Move(color=self.cursor.color),
                extra=StonelessReason.UNDO,
                is_new=False,
            )
        )
        self.fire_event(result)

    def resign(self, color: Status):
        self.fire_event(Ended(END_BY_RESIGN, color, GameResult()))

    def _set_cursor(self, move, no_fire=False):
        self._cursor = move
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.board = Board(self.board.boardsize)
        self._set_handicap()
        path = self.get_path()
        self._cursor = self.root
        for pmove in path:
            self.test_move(pmove, apply_result=True)
        if not no_fire:
            self.fire_event(
                CursorChanged(
                    MoveResult(
                        next_player=self.nextcolor, move=self.cursor, is_new=False
                    ),
                    self.board,
                )
            )

    def test_move(self, move, apply_result=False):
        is_new = True
        if child := self.cursor.children.get(move.pos):
            if child.color == move.color:
                move = child
                is_new = False

        if move.pos:
            result = self.board.result(move)
        else:
            extra = StonelessReason.PASS if move.is_pass else StonelessReason.ADD_STONES
            result = MoveResult(
                next_player=self.get_othercolor(self.nextcolor), move=move, extra=extra
            )
        result.is_new = is_new
        result.move = move
        result.next_player = result.next_player or self.get_othercolor(self.nextcolor)
        if apply_result:
            self._apply_result(result)

        return result

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

    def count(self):
        groups = count(self.board)
        res = self.ruleset.set_result(groups)
        self.fire_event(Counted(res, self.board))

    def toggle_status(self, pos):
        status = self.board.pos(pos).toggle_dead()
        group = self.board.analyze(pos, findkilled=False)[1]
        for x, y in group:
            if not self.board[x][y].is_empty():
                self.board[x][y] = status
        self.count()
