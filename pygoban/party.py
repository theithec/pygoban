from collections.abc import Callable
from dataclasses import dataclass

from .board import Color


class Member:
    def __init__(self, name="Unknown"):
        self.name = name


class Party:
    interact: Callable | None

    def __init__(self, color: Color, members: list[Member], name: str | None = None):
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
