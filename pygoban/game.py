from threading import Timer
from typing import Dict, Tuple

from . import END_BY_RESIGN, logging
from .board import Board, MoveResult
from .counting import counted_groups
from .events import Counted, CursorChanged, Ended, Reset
from .move import Empty, Move
from .rulesets import BaseRuleset, RuleViolation
from .sgf import INFO_KEYS
from .status import BLACK, WHITE, Status, get_othercolor


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
        self.root = Move(color=None, pos=Empty.ROOT)
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

    def _set_handicap(self):
        handicap = self.infos.get("HA")
        if not handicap:
            return
        positions = HANDICAPS.get(handicap, tuple())
        for pos in positions:
            self.board.pos(pos, BLACK)

    def add_listener(self, instance, event_classes, wait=False):
        for event_class in event_classes:
            self.registrations.setdefault(event_class, [])
            self.registrations[event_class].append((instance, wait))

    def fire_event(self, event):
        listeners = self.registrations.get(event.__class__, [])
        logging.debug("FIRE %s ->  %s", str(event), listeners)
        for listener, wait in listeners:
            wait = False
            if wait:
                listener.handle_game_event(event)
            else:
                Timer(0, lambda: listener.handle_game_event(event)).start()

    def _set_cursor(self, move, reset=None):
        self._cursor = move
        path = self.get_path()
        self.prisoners = {BLACK: 0, WHITE: 0}
        self.board = Board(self.board.boardsize)
        self._set_handicap()
        self._cursor = self.root
        for pmove in path:
            self.test_move(pmove, apply_result=True)
        event = CursorChanged(
            next_player=self.nextcolor,
            cursor=self.cursor,
            board=self.board,
            reset=reset,
        )
        self.fire_event(event)

    def test_move(self, move, apply_result=False):
        if child := self.cursor.children.get(move.pos):
            if child.color == move.color:
                move = child

        if not move.is_empty:
            result = self.board.result(move)
        else:
            result = MoveResult(move=move)
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
                # result.next_player = None
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
        logging.info("\n\nPlay %s %s", color, pos)
        move = Move(color, pos)
        if pos == Empty.RESIGN:
            self.resign(color)
            return None
        if pos == Empty.UNDO:
            if self.cursor.parent:
                self.undo()
            else:
                logging.info("Can not undo. No parent")
            return None
        else:
            result = self.test_move(move)
            try:
                self.ruleset.validate(result)
            except RuleViolation as err:
                logging.info("RuleViolation: %s", err)
                result.exception = err
                # result.next_player = color
            if not result.exception:
                self._apply_result(result)

            self.fire_event(
                CursorChanged(
                    next_player=self.nextcolor,
                    cursor=result.move,
                    board=self.board,
                )
            )
        # for testing
        return result

    def count(self, is_final=False):
        groups = counted_groups(self.board)
        result = self.ruleset.set_result(groups)
        if is_final:
            btotal = result.points[BLACK] + result.prisoners[BLACK]
            wtotal = result.points[WHITE] + result.prisoners[WHITE]
            color = BLACK if btotal > wtotal else WHITE
            msg = "{color}+%s" % str(max(wtotal, btotal) - min(wtotal, btotal))
            event = Ended(
                msg=msg,
                color=color,
                points=result.points,
                prisoners=result.prisoners,
            )
        else:
            event = Counted(
                points=result.points, prisoners=result.prisoners, board=self.board
            )
        self.fire_event(event)

    def toggle_status(self, pos):
        status = self.board.pos(pos).toggle_dead()
        group = self.board.analyze(pos, findkilled=False)[1]
        for x, y in group:
            if not self.board[x][y].is_empty():
                self.board[x][y] = status
        self.count()

    def undo(self):
        curr = self.cursor
        logging.debug("UNDO0.  %s", str(curr))
        while parent := curr.parent:
            if parent:
                curr = parent
            else:
                break
            if parent.is_empty and not parent.pos == Empty.ROOT:
                continue
            break
        if not curr.is_empty or curr.pos == Empty.ROOT:
            logging.info("UNDO. Set Cursor: %s", curr)
            self._set_cursor(curr, reset=Reset.UNDO)
        else:
            logging.info("CAN NOT UNDO. Cursor: %s", self.cursor)

    def resign(self, color: Status):
        self.fire_event(Ended(msg=END_BY_RESIGN, color=color))
