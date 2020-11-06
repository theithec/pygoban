from .status import BLACK, BLACK_LIB, DEAD_BLACK, DEAD_WHITE, EMPTY, WHITE, WHITE_LIB


def check(x, y, board, checked, group=None):
    group = group or {"owner": None, "coords": set()}
    status = board[x][y]
    if status == EMPTY or status in (DEAD_BLACK, DEAD_WHITE, BLACK_LIB, WHITE_LIB):
        group["coords"].add((x, y))
        checked.add((x, y))
    else:
        if group["owner"] is None:
            group["owner"] = status
        elif group["owner"] != status:
            group["owner"] = False
    for adj in board._adjacent_ins((x, y)):
        ax, ay = adj
        if (ax, ay) in checked:
            continue
        elif status == EMPTY or status in (
            DEAD_BLACK,
            DEAD_WHITE,
            BLACK_LIB,
            WHITE_LIB,
        ):
            check(ax, ay, board, checked, group)
    return group


def count(board):
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

    for group in groups:
        if group["owner"] == BLACK:
            status = BLACK_LIB
        elif group["owner"] == WHITE:
            status = WHITE_LIB
        for coord in group["coords"]:
            x, y = coord
            if board[x][y] == EMPTY:
                board[x][y] = status
    return groups
