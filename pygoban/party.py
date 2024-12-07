from dataclasses import dataclass
from typing import Callable, List, Optional

from .board import Color
from .results import ActionResult

# from pygoban.gtp import GTPConn


class Member:
    def __init__(self, name="Unknown"):
        self.name = name

    # def receive_game_event(self, result: ActionResult):
    #    print(self, result)


class Party:
    interact: Optional[Callable]

    def __init__(self, color: Color, members: List[Member], name: Optional[str] = None):
        self.color = color
        self.name = name or str(color)
        self.members = members
        # self.interact = None

    # def receive_game_event(self, result: ActionResult):
    #    for member in self.members:
    #        member.receive_game_event(result)

    # def send(self, *args, **kwargs) -> None:
    #    self.interact(self.color, *args, **kwargs)  # pylint: disable=not-callable  # type:ignore

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
