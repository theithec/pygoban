from pygoban import Ruleset, Node, coords


def to_sgf(node: Node, txt="(") -> str:
    print("ST", node, txt)
    col = node.color.short() if node.color else None
    if col:
        pos = coords.pos_to_sgf(node.pos) if node.pos else ""
        txt = f"\n;{col}[{pos}]"
    for child in node.children:
        if len(node.children) > 1:
            txt += "("
        txt += to_sgf(child, txt)
    if not node.children:
        txt += ")"

    return txt


def write(cursor: Node, ruleset: Ruleset):
    curr = cursor.root()
    print(
        f"""(FF[4]GM[1]SZ[{ruleset.boardsize}]KM[{ruleset.komi}]HA[{ruleset.handicap}]
    {to_sgf(curr)})"""
    )
    print("...")
