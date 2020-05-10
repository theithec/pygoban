from typing import List
from .status import STATUS, Status


class MoveList(list):
    '''sgf-like output'''
    def __str__(self):
        items = [str(item) for item in self]
        return "(%s)" % " ".join(items)


class Move:
    def __init__(self, color: Status, x=None, y=None, parent=None):
        self.x = -1 if x is None else x
        self.y = y
        self.color = color
        self.children: List[Move] = []
        if parent:
            parent.children.append(self)

        self.parent = parent

        self.is_pass = self.x == -1
        self.is_root = self.color is None
        self.comments = []
        self.decorations = {}

    def __del__(self):
        if self.parent:
            self.parent.children.pop(self.parent.children.index(self))

    def __str__(self):
        if self.is_root:
            return "ROOT"

        txt = "%s={}" % self.color.intval
        if self.is_pass:
            return txt.format(" pass ")
        else:
            return txt.format("%s,%s" % (self.x, self.y))

    def get_decorated_variations(self, tree=None):
        '''all variations'''
        tree = MoveList() if tree is None else tree
        tree.append(self)

        if len(self.children) == 1:
            self.children[0].get_variations(tree)
        else:
            for child in self.children:
                tree.append(child.get_variations())

        return tree
