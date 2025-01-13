from dataclasses import dataclass
from typing import Callable, List, Optional

from .board import Color

# from pygoban.gtp import GTPConn


class Member:
    def __init__(self, name="Unknown"):
        self.name = name


class Party:
    interact: Optional[Callable]

    def __init__(self, color: Color, members: List[Member], name: Optional[str] = None):
        self.color = color
        self.name = name or str(color)
        self.members = members
        # self.interact = None

    def __str__(self):
        return f"Player {self.color.name}"


@dataclass()
class Parties:
    black: Party
    white: Party

    def __getitem__(self, key):
        if key == Color.BLACK:
            return self.black
        if key == Color.WHITE:
            return self.white
        raise KeyError(key)
