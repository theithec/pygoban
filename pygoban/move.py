from typing import Dict
from collections import OrderedDict
from typing import Any, Dict, List

from .status import Status
from .coords import gtp_coord_to_sgf


class MoveList(list):
    '''sgf-like output'''

    def __str__(self):
        items = [str(item) for item in self]
        return "(%s)" % " ".join(items)

class Move:
    def __init__(self, color: Status, coord, parent=None):
        self.coord = coord
        self.color = color
        self.children: Dict[str, "Move"] = OrderedDict()

        self._parent = None
        if parent:
            self.parent = parent

        self.is_pass = not self.coord
        self.is_root = self.color is None
        self.comments: List[str] = []
        self.decorations: Dict[Any, Any] = {}

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, _parent):
        self._parent = _parent
        self._parent.children[self.coord] = self

    def __del__(self):
        if self.parent:
            self.parent.children.pop(self.coord)

    def __str__(self):
        if self.is_root:
            return ""
        txt = ";{color_char}[{val}]"
        if self.is_pass:
            val = ""
        else:
            val = gtp_coord_to_sgf(self.coord)

        txt = txt.format(color_char=self.color.shortval, val=val)
        for comment in self.comments:
            if comment:
                txt += f"C[{comment}]"
        return txt

    #def get_decorated_variations(self, tree=None):
    #    '''all variations'''
    #    tree = MoveList() if tree is None else tree
    #    tree.append(self)

    #    if len(self.children) == 1:
    #        self.children[0].get_variations(tree)
    #    else:
    #        for child in self.children:
    #            tree.append(child.get_variations())

    #    return tree

    #@classmethod
    #def pass_(cls, color: Status, parent: "Move"):
    #    return cls(color, -1, -1, parent)
