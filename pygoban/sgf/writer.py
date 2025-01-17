from pygoban import Color, Marker, Node, Ruleset, coords, Pos

p2s = coords.pos_to_sgf


def to_sgf(node: Node) -> str:
    print("N", node, node.annos)
    col = node.color.short() if node.color else None
    txt = ""
    if col:
        sgfpos = p2s(node.pos) if node.pos else ""
        txt += f"\n;{col}[{sgfpos}]"
    if comment := node.annos.comment:
        txt += f"C[{comment}]"
    for chars in (node.annos.chars, node.annos.numbers):
        if chars := node.annos.chars:
            txt += "LB"
            for pos, ctxt in chars.items():
                sgfpos = p2s(pos)
                txt += f"[{sgfpos}:{ctxt}]"
    markers: dict[Marker, set[str]] = {marker: set() for marker in Marker}
    for pos, marker in node.annos.markers.items():
        sgfpos = p2s(pos)
        markers[marker].add(sgfpos)
    for marker, pos_set in markers.items():
        if not pos_set:
            continue
        txt += marker.name
        for sgfpos in pos_set:
            txt += f"[{sgfpos}]"
    for shapes, key in ((node.annos.arrows, "AR"), (node.annos.lines, "LN")):
        if not shapes:
            continue
        txt += key
        for posstart, posend in shapes:
            txt += f"[{p2s(posstart)}:{p2s(posend)}]"
    if node.annos.stones:
        stones: dict[Color, list[Pos]] = {Color.BLACK: [], Color.WHITE: [], Color.EMPTY: []}
        for pos, color in node.annos.stones.items():
            stones[color].append(pos)
        for color, pos_list in stones.items():
            if not pos_list:
                continue
            txt += "A" + color.short()
            txt += "".join([f"[{p2s(pos)}]" for pos in pos_list])

    for child in node.children:
        if len(node.children) > 1:
            txt += "("
        txt2 = to_sgf(child)
        txt += txt2
        if len(node.children) > 1:
            txt += "\n)"

    return txt


def write(cursor: Node, ruleset: Ruleset) -> str:
    # print("I", ruleset.info)
    info = ruleset.info
    curr = cursor.root()
    return (
        f"(;GM[1]FF[4]CA[UTF-8]SZ[{ruleset.boardsize}]KM[{ruleset.komi}]HA[{ruleset.handicap}]"
        f"PB[{info.names[Color.BLACK]}]PW[{info.names[Color.WHITE]}]"
        f"{to_sgf(curr)})"
    )
