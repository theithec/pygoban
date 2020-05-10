from copy import deepcopy
from typing import Dict


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

KO = Status(-1, "Ko", "?")
EMPTY = Status(0, "Empty", "+")
BLACK = Status(1, "Black")
WHITE = Status(2, "White")
DEAD_BLACK = Status(3, "b")
DEAD_WHITE = Status(4, "w")

STATUS = {
    int(sts): sts for sts in (KO, EMPTY, BLACK, WHITE, DEAD_BLACK, DEAD_WHITE)
}
