class Pos(tuple):
    """A handcrafted named tuple"""

    def __new__(cls, x, y):
        return super().__new__(cls, (x, y))

    def __init__(self, *_args, **_kwargs):
        self.x = self[0]
        self.y = self[1]
