from . import STATUS


class Move:
    def __init__(self, col_id, x=None, y=None, parent=None):
        self.x = -1 if x is None else x
        self.y = y
        self.col_id = col_id
        self.children = []
        if parent:
            parent.children.append(self)

        self.parent = parent

        self.is_pass = self.x == -1
        self.is_root = self.col_id is None

    def __del__(self):
        if self.parent:
            self.parent.children.pop(self.parent.children.index(self))

    def __str__(self):
        if self.is_root:
            return "ROOT"

        txt = "%s={}" % STATUS[self.col_id]
        if self.is_pass:
            return txt.format(" pass ")
        else:
            return txt.format("%s,%s" % (self.x, self.y))
