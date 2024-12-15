from . import Pos


def letter_from_int(val: int, skip_i=False) -> str:
    summand = 66 if val > 7 and skip_i else 65
    return chr(summand + val)


def int_from_letter(val, skip_i=False) -> int:
    res = ord(val.upper()) - 65
    if res > 7 and skip_i:
        res -= 1
    return res


def gtp_coord_to_pos(coord: str, boardsize) -> Pos:
    x = int_from_letter(coord[0], skip_i=True)
    y = boardsize - int(coord[1:])
    return Pos(x, y)


def pos_to_gtp_coord(pos: Pos, boardsize: int) -> str:
    v = letter_from_int(pos[0], skip_i=True) + str(boardsize - int(pos[1]))
    return v


def sgf_to_poslist(coord: str) -> list[Pos]:
    poslist = []

    def getpos(coord):
        pos = Pos(int_from_letter(coord[0], False), int_from_letter(coord[1], False))
        assert pos[0] < 19
        return pos

    if ":" in coord:
        startcoord, endcoord = coord.split(":")
        startpos = getpos(startcoord)
        endpos = getpos(endcoord)
        assert startpos[0] <= endpos[0] and startpos[1] <= endpos[1]
        for x in range(startpos[0], endpos[0] + 1):
            for y in range(startpos[1], endpos[1] + 1):
                poslist.append(Pos(x, y))
    else:
        poslist.append(getpos(coord))
    return poslist


def sgf_to_pos(coord: str) -> Pos:
    assert ":" not in coord, "Use sgflist_to_pos"
    return sgf_to_poslist(coord)[0]


def pos_to_sgf(pos: Pos) -> str:
    return letter_from_int(pos[0], False) + letter_from_int(pos[1], False)
