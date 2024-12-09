from copy import deepcopy
from typing import Dict, Optional, Tuple

from .board import Board, Color, Pos
from .results import ActionResult, ActionType, StoneResult
from .stone import Annotations, Stone

HANDICAPS: Dict[int, Tuple] = {0: tuple(), 2: ((3, 15), (15, 3))}
HANDICAPS[3] = HANDICAPS[2] + ((3, 3),)
HANDICAPS[4] = HANDICAPS[3] + ((15, 15),)
HANDICAPS[5] = HANDICAPS[4] + ((9, 9),)
HANDICAPS[6] = HANDICAPS[4] + (
    (3, 9),
    (15, 9),
)
HANDICAPS[7] = HANDICAPS[6] + ((9, 9),)
HANDICAPS[8] = HANDICAPS[6] + ((9, 3), (9, 15))
HANDICAPS[9] = HANDICAPS[8] + ((9, 9),)


class StonesController:
    cursor: Stone
    total_dead: Dict[Color, int]

    def __init__(self, boardsize: int, handicap: int = 0) -> None:
        self.total_dead = {Color.BLACK: 0, Color.WHITE: 0}
        self.handicap = handicap
        self.boardsize = boardsize
        self.board = Board(self.boardsize)
        self.root: Stone = Stone(color=Color.EMPTY)
        # self.set_cursor(self.root)

    def set_cursor(self, stone: Stone) -> ActionResult:
        if not stone.parent:
            self.root = stone
        self.cursor = self.root
        self.total_dead = {Color.BLACK: 0, Color.WHITE: 0}
        self.board = Board(self.boardsize)
        self.root.apply_permanent_annos(self.board)
        for x, y in HANDICAPS[self.handicap]:
            self.board.intersection(Pos(x, y), Color.BLACK)
        result = None
        for stone_ in stone.path():
            # assert stone_.pos
            result = self.get_result(
                color=stone_.color,
                pos=stone_.pos,
                actiontype=ActionType.STONE,
                annos=stone_.annos,
            )
            self.apply_result(result)

        if not result:  # path is empty -> only root
            next_color = Color.BLACK if not self.handicap else Color.WHITE
            result = ActionResult(
                type=ActionType.RESET,
                board=self.board,
                stone_result=StoneResult(stone=self.root, next_color=next_color),
            )

        return result

    def apply_result(self, result: ActionResult):
        oldcursor = self.cursor
        assert result.stone_result
        stone_result = result.stone_result
        self.cursor = stone_result.stone
        self.cursor.set_parent(oldcursor)
        self.total_dead[
            Color.BLACK if stone_result.stone.color == Color.WHITE else Color.WHITE
        ] += len(stone_result.killed)
        result.total_dead = self.total_dead
        self.board = result.board
        for pos in stone_result.killed:
            self.board.intersection(pos, Color.EMPTY)
        stone_result.stone.apply_permanent_annos(self.board)

    def get_result(
        self,
        color: Color,
        pos: Pos | None,
        actiontype: ActionType,
        annos: Annotations | None = None,
    ) -> ActionResult:
        assert self.board
        boardcpy = deepcopy(self.board)

        if pos:
            boardcpy.intersection(pos, color)
            # group, killed, libs = boardcpy.analyze(pos)[1:4]
            killed, libs = boardcpy.analyze(pos)
        else:
            killed = set()
            libs = set()
        stone = None
        for child in self.cursor.children:
            if child.pos == pos and child.color == color:
                if not (pos or color) and annos and annos != child.annos:
                    continue
                stone = child
                break
        else:
            stone = Stone(color=color, pos=pos)

        next_color = color.other()

        return ActionResult(
            type=actiontype,
            board=boardcpy,
            stone_result=StoneResult(stone=stone, killed=killed, libs=libs, next_color=next_color),
        )
