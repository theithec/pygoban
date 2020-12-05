def letter_from_int(val):
    return chr(65 + val)


def char_to_int(char, skip_i=True):
    ival = ord(char.upper())
    diff = 66 if skip_i and ival > 72 else 65
    return ival - diff


def array_indexes(coords, boardsize):
    xcoord = boardsize - int(coords[1:])
    ycoord = char_to_int(coords[0])
    assert 0 <= xcoord < boardsize, f"{xcoord}, {coords}"
    assert 0 <= ycoord < boardsize, f"{ycoord}, {coords}"
    res = xcoord, ycoord
    return res


def gtp_coords(x, y, boardsize):
    return "%s%s" % (letter_from_int(y), boardsize - x)


def sgf_to_pos(coord):
    return char_to_int(coord[1], False), char_to_int(coord[0], False)


def pos_to_sgf(coord, boardsize):
    x = letter_from_int(coord[0])
    y = letter_from_int(coord[1])
    return f"{y}{x}".lower()
