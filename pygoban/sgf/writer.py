from typing import Dict
from pygoban.move import Move, Empty
from pygoban.coords import pos_to_sgf
from . import INFO_KEYS, TR, MA, CR, SQ

SYM_MAP = {TR: "TR", MA: "MA", CR: "CR", SQ: "SQ"}


def _to_sgf(move: Move, boardsize, level=0, txt=""):
    if move.color:
        dist = "\t" * level
        if not move.is_empty:
            coord = pos_to_sgf(move.pos)
        elif move.pos == Empty.UNDO:
            return txt, level
        else:
            coord = ""
        txt += f"\n{dist};{move.color.shortval}[{coord}]"

    for comment in move.extras.comments:
        txt += f"C[{comment}]"

    collect = {}
    for key, value in move.extras.decorations.items():
        if cmd := SYM_MAP.get(value):
            collect.setdefault(cmd, [])
            collect[cmd].append(pos_to_sgf(key))
        else:
            collect.setdefault("LB", [])
            collect["LB"].append(pos_to_sgf(key) + ":" + value)
    for key, value in collect.items():
        if cmd in SYM_MAP.values():
            txt += cmd + "[" + "][".join(value) + "]"
        else:
            txt += "LB" + "[" + "][".join(value) + "]"

    has_variation = len(move.children) > 1
    for child in move.children.values():
        if has_variation:
            dist = "\t" * level
            txt += f"\n{dist}("
            level += 1
        txt, level = _to_sgf(child, boardsize, level, txt)
        if has_variation:
            level -= 1
            dist = "\t" * level
            txt += f"\n{dist})"
    return txt, level


def to_sgf(infos: Dict, root: Move):
    # print("infos", infos, root)
    txt = "(;"
    for key in INFO_KEYS:
        val = infos.get(key)
        if val is not None:
            txt += f"{key}[{val}]"

    txt += _to_sgf(root, boardsize=infos["SZ"])[0]
    txt += ")"
    return txt
