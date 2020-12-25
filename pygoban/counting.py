from typing import Dict
from .status import Status, BLACK, BLACK_LIB, EMPTY, WHITE, WHITE_LIB


def check(x, y, board, checked, group=None):
    group = group or {"owner": None, "coords": set()}
    status = board[x][y]
    if status == EMPTY or status.is_owned():
        group["coords"].add((x, y))
        checked.add((x, y))
    else:
        if group["owner"] is None:
            group["owner"] = status
        elif group["owner"] != status:
            group["owner"] = False
    for adj in board.adjacent_ins((x, y)):
        adx, ady = adj
        if (adx, ady) in checked:
            continue
        if status == EMPTY or status.is_owned():
            check(adx, ady, board, checked, group)
    return group


def counted_groups(board):
    groups = []
    boardrange = range(board.boardsize)
    checked = set()
    for x in boardrange:
        for y in boardrange:
            if board[x][y] in (BLACK_LIB, WHITE_LIB):
                board[x][y] = EMPTY
            if (x, y) not in checked:
                group = check(x, y, board, checked)
                if group["owner"] and group["coords"]:
                    groups.append(group)

    points: Dict[Status, int] = {BLACK: 0, WHITE: 0}
    prisoners: Dict[Status, int] = {BLACK: 0, WHITE: 0}
    for group in groups:
        owner = group["owner"]
        for coord in group["coords"]:
            x, y = coord
            if board[x][y] == EMPTY:
                status = BLACK_LIB if owner == BLACK else WHITE_LIB
                board[x][y] = status
                points[owner] += 1
            else:
                status = board[x][y]
            if (not status.is_empty()) and status != owner:
                prisoners[owner] += 1
                points[owner] += 1
    return groups
