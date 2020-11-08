class Status:
    def __init__(self, intval, strval, shortval=None):
        self.intval = intval
        self.strval = strval
        self.shortval = shortval or strval[0]

    def __int__(self):
        return self.intval

    def __str__(self):
        return self.strval

    def __repr__(self):
        return self.strval

    def short(self):
        return self.shortval

    def toggle_dead(self):
        assert self.intval in (1, 2, 3, 4)
        return STATUS[self.intval + (2 if self.intval < 3 else -2)]

    def is_empty(self):
        return self == EMPTY or self == BLACK_LIB or self == WHITE_LIB

    def is_owned(self):
        return self in (DEAD_BLACK, DEAD_WHITE, BLACK_LIB, WHITE_LIB)


KO = Status(-1, "Ko", "?")
EMPTY = Status(0, "Empty", "+")
BLACK = Status(1, "Black")
WHITE = Status(2, "White")
DEAD_BLACK = Status(3, "b")
DEAD_WHITE = Status(4, "w")
BLACK_LIB = Status(5, "B")
WHITE_LIB = Status(6, "W")
STATUS = {int(sts): sts for sts in (KO, EMPTY, BLACK, WHITE, DEAD_BLACK, DEAD_WHITE)}
