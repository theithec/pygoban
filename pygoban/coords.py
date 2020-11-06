def letter_coord_from_int(pos_, boardsize):
    assert pos_ < boardsize
    i = (66 if pos_ > 7 else 65) + pos_
    return chr(i)


def array_indexes(coords, boardsize):
    yord = ord(coords[0].upper())
    ycoord = yord - (66 if yord > 72 else 65)
    xcoord = boardsize - int(coords[1:])
    assert 0 <= xcoord < boardsize, f"{xcoord}, {coords}"
    assert 0 <= ycoord < boardsize, f"{ycoord}, {coords}"
    res = xcoord, ycoord
    return res


def gtp_coords(x, y, boardsize):
    return "%s%s" % (letter_coord_from_int(y, boardsize), boardsize - x)


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
