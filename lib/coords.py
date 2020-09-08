def letter_coord_from_int(pos, boardsize):
    assert pos < boardsize
    i = (66 if pos > 7 else 65) + pos
    return chr(i)


def array_indexes(coords, boardsize):
    yord = ord(coords[0].upper())
    ycoord = yord - (66 if yord > 72 else 65)
    xcoord = boardsize - int(coords[1:])
    assert 0 <= xcoord < boardsize, f"{xcoord}, {coords}"
    assert 0 <= ycoord < boardsize, f"{ycoord}, {coords}"
    res = xcoord, ycoord
    print("to array", coords, "->", res)
    return res


def sgf_coords(x, y, boardsize):
    res = "%s%s" % (
        letter_coord_from_int(y, boardsize), boardsize - x)
    print("to coord", x, y, "->", res)
    return res
