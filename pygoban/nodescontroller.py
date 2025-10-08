from copy import deepcopy

from .board import Board, Color, Pos
from .results import TurnDone
from .node import Annotations, Node

HANDICAPS: dict[int, tuple] = {0: tuple(), 2: ((3, 15), (15, 3))}
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


class NodesController:
    cursor: Node
    total_dead: dict[Color, int]

    def __init__(self, boardsize: int, handicap: int = 0) -> None:
        self.total_dead = {Color.BLACK: 0, Color.WHITE: 0}
        self.handicap = handicap
        self.boardsize = boardsize
        self.board = Board(self.boardsize)
        self.root: Node = Node(color=Color.EMPTY)
        self.default_next_color = Color.BLACK if not self.handicap else Color.WHITE

    def set_cursor(self, stone: Node) -> TurnDone:
        if not stone.parent:
            self.root = stone
        self.cursor = self.root
        self.total_dead = {Color.BLACK: 0, Color.WHITE: 0}
        self.board = Board(self.boardsize)
        self.cursor.apply_permanent_annos(self.board)
        for x, y in HANDICAPS[self.handicap]:
            self.board.intersection(Pos(x, y), Color.BLACK)
        result = None
        for stone_ in stone.path():
            result = self.get_result(
                color=stone_.color, pos=stone_.pos, annos=stone_.annos, use_copy=False
            )
            self.apply_result(result)

        if not result:  # path is empty -> only root
            result = TurnDone(
                board=self.board,
                node=self.root,
                next_color=self.default_next_color,
            )
        result.reset = True
        return result

    def apply_result(self, result: TurnDone):
        oldcursor = self.cursor
        self.cursor = result.node
        self.cursor.set_parent(oldcursor)
        self.total_dead[
            Color.BLACK if result.node.color == Color.WHITE else Color.WHITE
        ] += len(result.killed)
        result.total_dead = self.total_dead
        self.board = result.board
        for pos in result.killed:
            self.board.intersection(pos, Color.EMPTY)
        result.node.apply_permanent_annos(self.board)

    def get_result(
        self,
        color: Color,
        pos: Pos | None,
        annos: Annotations | None = None,
        use_copy=True,
    ) -> TurnDone:
        """set use_copy to False if no validation is required"""
        assert self.board
        boardcpy = deepcopy(self.board) if use_copy else self.board

        if pos:
            boardcpy.intersection(pos, color)
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
            stone = Node(color=color, pos=pos)

        next_color = color.other() if not color.is_empty() else self.default_next_color

        return TurnDone(
            board=boardcpy,
            node=stone,
            next_color=next_color,
            killed=killed,
            libs=libs,
        )
