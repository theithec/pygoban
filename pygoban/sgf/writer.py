from pygoban import Color, Marker, Node, Ruleset, coords


def to_sgf(node: Node) -> str:
    def _to_sgf(node: Node, txt="", found_children=False) -> tuple[str, bool]:
        col = node.color.short() if node.color else None
        txt = ""
        if col:
            sgfpos = coords.pos_to_sgf(node.pos) if node.pos else ""
            txt += f"\n;{col}[{sgfpos}]"
        if comment := node.annos.comment:
            txt += f"C[{comment}]"
        for chars in (node.annos.chars, node.annos.numbers):
            if chars := node.annos.chars:
                txt += "LB"
                for pos, ctxt in chars.items():
                    sgfpos = coords.pos_to_sgf(pos)
                    txt += f"[{sgfpos}:{ctxt}]"
        markers: dict[Marker, set[str]] = {marker: set() for marker in Marker}
        for pos, marker in node.annos.markers.items():
            sgfpos = coords.pos_to_sgf(pos)
            markers[marker].add(sgfpos)
        for marker, pos_set in markers.items():
            if not pos_set:
                continue
            txt += marker.name
            for sgfpos in pos_set:
                txt += f"[{sgfpos}]"
        for child in node.children:
            found_children = True
            if len(node.children) > 1:
                txt += "("
            txt2, found_children = _to_sgf(child, txt, found_children=found_children)
            txt += txt2
        if not node.children:
            txt += "\n)"

        return txt, found_children

    txt, found_children = _to_sgf(node)
    if found_children:
        txt += ")"
    return txt


def write(cursor: Node, ruleset: Ruleset) -> str:
    # print("I", ruleset.info)
    info = ruleset.info
    curr = cursor.root()
    return (
        f"(;GM[1]FF[4]CA[UTF-8]SZ[{ruleset.boardsize}]KM[{ruleset.komi}]HA[{ruleset.handicap}]"
        f"PB[{info.names[Color.BLACK]}]PW[{info.names[Color.WHITE]}]" + to_sgf(curr)
    )
