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
        def sgf_int_from_letter(letter: str) -> int:
            if "a" <= letter <= "z":
                return ord(letter) - ord("a")
            if "A" <= letter <= "Z":
                return ord(letter) - ord("A") + 26
            raise ValueError(f"Invalid SGF coordinate: {coord}")

        return Pos(sgf_int_from_letter(coord[0]), sgf_int_from_letter(coord[1]))

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
    def sgf_letter_from_int(value: int) -> str:
        if 0 <= value < 26:
            return chr(ord("a") + value)
        if 26 <= value < 52:
            return chr(ord("A") + value - 26)
        raise ValueError(f"SGF coordinate out of range: {value}")

    return sgf_letter_from_int(pos[0]) + sgf_letter_from_int(pos[1])
