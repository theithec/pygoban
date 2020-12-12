from threading import Timer
from typing import Dict, Tuple

from .board import Board, MoveResult
from .move import Move, Empty
from .rulesets import BaseRuleset, RuleViolation
from .status import BLACK, WHITE, Status, get_othercolor
from .events import MovePlayed, CursorChanged, MovesReseted, Counted, Ended
from .counting import count
from .sgf import INFO_KEYS
from . import logging, END_BY_RESIGN


HANDICAPS: Dict[int, Tuple] = {2: ((3, 3), (15, 15))}
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
        self.root = Move(color=None, pos=Empty.FIRST_MOVE)
        self._cursor = self.root
        self.registrations = {}

    @property
    def boardsize(self):
        return self.board.boardsize

    @property
    def cursor(self):
        return self._cursor

    @property
    def nextcolor(self):
        if not self.cursor.parent and int(self.infos.get("HA", 0)) > 1:
            return WHITE
        return get_othercolor(self.cursor.color)

    def start(self):
        self._set_cursor(self.cursor)
        self.fire_event(MovesReseted(self.root))
        self.fire_event(
            MovePlayed(
                next_player=self.nextcolor,
                move=self.cursor,
                is_new=self.cursor.is_root,
            )
        )

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
            Timer(0, lambda: listener.handle_game_event(event)).start()

    def _set_cursor(self, move, no_fire=False):
        self._cursor = move
        path = self.get_path()
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.board = Board(self.board.boardsize)
        self._set_handicap()
        is_new = self._cursor == self.root
        self._cursor = self.root
        for pmove in path:
            self.test_move(pmove, apply_result=True)
        if not no_fire:
            self.fire_event(
                CursorChanged(
                    next_player=self.nextcolor,
                    cursor=self.cursor,
                    board=self.board,
                    is_new=is_new,
                )
            )

    def test_move(self, move, apply_result=False):
        is_new = True
        if child := self.cursor.children.get(move.pos):
            if child.color == move.color:
                move = child
                is_new = False

        if not move.is_empty:
            result = self.board.result(move)
        else:
            result = MoveResult(next_player=get_othercolor(self.nextcolor), move=move)
            result.is_new = is_new
        result.move = move
        result.next_player = result.next_player or get_othercolor(
            self.nextcolor
        )  # OLD cursor!
        if apply_result:
            self._apply_result(result)
        return result

    def _apply_result(self, result):
        move = result.move
        if not move.is_empty and move.color:
            self.board.apply_result(result)
            self.prisoners[move.color] += len(result.killed)
        elif move.is_pass:
            if (
                self.cursor.is_pass
                and self.cursor.parent
                and self.cursor.parent.is_pass
            ):
                result.next_player = None
                self.count()
        elif move.pos == Empty.RESIGN:
            self.resign(move.color)
        if move.extras.has_stones():
            for status in (BLACK, WHITE):
                poss = move.extras.stones[status]
                for pos in poss:
                    x, y = pos
                    self.board[x][y] = status
        if not move.parent:
            move.parent = self.cursor

        if not move.pos == Empty.UNDO:
            self._cursor = result.move

    def get_path(self):
        return self.cursor.get_path()

    def tree(self, curr=None, level=1):
        print(
            "\t" * level,
            curr,
            " Parent: ",
            curr.parent if curr else "-",
            "!CURSOR!" if curr == self.cursor else "",
        )
        curr = curr or self.root
        children = curr.children
        if children:
            level += 1
            for child in children.values():
                self.tree(child, level)

    def get_callbacks(self):
        return {
            "play": self.play,
            "get_prisoners": lambda: self.prisoners,
            "set_cursor": self._set_cursor,
            "toggle_status": self.toggle_status,
            "count": self.count,
        }

    def play(self, color: Status, pos):
        # import pudb; pudb.set_trace()
        logging.info("Play %s %s", color, pos)
        move = Move(color, pos)
        if pos == Empty.UNDO and self.cursor != self.root:
            self.undo()
            return

        if pos == Empty.RESIGN:
            self.resign(color)
            return
        result = self.test_move(move)
        try:
            self.ruleset.validate(result)
        except RuleViolation as err:
            # logging.info("RuleViolation: %s", err)
            result.exception = err
            result.next_player = color
        if not result.exception:
            self._apply_result(result)

        if not move.pos == Empty.UNDO:
            self.fire_event(
                CursorChanged(
                    next_player=result.next_player,
                    cursor=result.move,
                    is_new=result.is_new,
                    board=self.board,
                )
            )
        self.fire_event(
            MovePlayed(
                **{
                    key: getattr(result, key)
                    for key in ("next_player", "move", "is_new")
                }
            )
        )
        return result

    def count(self):
        groups = count(self.board)
        result = self.ruleset.set_result(groups)
        self.fire_event(
            Counted(points=result.points, prisoners=result.prisoners, board=self.board)
        )

    def toggle_status(self, pos):
        status = self.board.pos(pos).toggle_dead()
        group = self.board.analyze(pos, findkilled=False)[1]
        for x, y in group:
            if not self.board[x][y].is_empty():
                self.board[x][y] = status
        self.count()

    def undo(self):
        old_color = self.cursor.color
        curr = self.cursor
        while (parent := curr.parent) :
            if parent:
                curr = parent
            else:
                break
            if parent.is_empty and not parent.pos == Empty.FIRST_MOVE:
                continue
            break
        if not curr.is_empty or curr.pos == Empty.FIRST_MOVE:
            logging.info("UNDO. Set Cursor: %s", curr)
            self._set_cursor(curr)
        else:
            logging.info("CAN NOT UNDO. Cursor: %s", self.cursor)

    def resign(self, color: Status):
        self.fire_event(Ended(msg=END_BY_RESIGN, color=get_othercolor(color)))
