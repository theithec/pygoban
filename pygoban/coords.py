def letter_coord_from_int(pos_, boardsize):
    assert pos_ < boardsize
    i = (66 if pos_ > 7 else 65) + pos_
    return chr(i)


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
    return "%s%s" % (letter_coord_from_int(y, boardsize), boardsize - x)


def sgf_to_pos(coord):
    return char_to_int(coord[0], False), char_to_int(coord[1], False)


def pos_to_sgf(coord, boardsize):
    x = letter_coord_from_int(coord[0], boardsize)
    y = boardsize - coord[1]
    return f"{x}{y}"


def sgf_coord_to_gtp(pos, boardsize):
    xchar, ychar = pos
    yord = ord(xchar)
    if yord >= 105:
        yord += 1
    xchar = chr(yord).upper()
    y = 96 - ord(ychar) + boardsize + 1
    coord = f"{xchar}{y}"
    return coord


def gtp_coord_to_sgf(pos):
    xnum = ord(pos[0].lower())
    ynum = 96 + int(pos[1:])
    if xnum > 105:
        xnum -= 1
    xval = chr(ynum)
    return chr(xnum) + xval
