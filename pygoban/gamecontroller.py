from typing import Type, TypeVar
import logging

from .board import Color, Marker
from .game import Game, Node
from .pos import Pos
from .receivers import BaseReceiver

G = TypeVar("G", bound="GameController")


class GameController:
    receiver: BaseReceiver

    def __init__(self, game: Game) -> None:
        self.ruleset = game.ruleset
        self.__game = game
        self._subs: set[GameController] = set()
        self.delete_requested = False

    @property
    def last_stone(self) -> Node:
        assert self.receiver.last_turn
        return self.receiver.last_turn.node

    def start(self, receiver: BaseReceiver, node: Node | None = None) -> None:
        self.receiver = receiver
        self.__game.start([self.receiver], node=node)

    def play(self, color: Color, pos: Pos | None = None):
        self.__game._place(color=color, pos=pos)  # pylint: disable=protected-access

    def set_cursor(self, node: Node):
        self.__game._reset(node)  # pylint: disable=protected-access

    def do_prev_variation(self) -> None:
        curr = self.last_stone
        while curr:
            if (not curr.parent) or len(curr.children) > 1:
                break
            curr = curr.parent
        self.set_cursor(curr)

    def do_next_variation(self) -> None:
        curr = self.last_stone
        while curr:
            if not curr.children or len(curr.children) > 1:
                break
            curr = curr.children[0]
        self.set_cursor(curr)

    def _do_sibling(self, direction: int):
        if not self.last_stone.parent or len(children := self.last_stone.parent.children) == 1:
            return
        index = children.index(self.last_stone) + direction
        if 0 <= index < len(children):
            self.set_cursor(children[index])

    def do_left_sibling(self):
        self._do_sibling(-1)

    def do_right_sibling(self):
        self._do_sibling(1)

    def do_prev_stone(self) -> None:
        if not self.last_stone.parent:
            return
        self.set_cursor(self.last_stone.parent)

    def do_next_stone(self) -> None:
        if not self.last_stone.children:
            return
        self.set_cursor(self.last_stone.children[0])

    def do_first_stone(self) -> None:
        self.set_cursor(self.last_stone.root())

    def do_pass(self) -> None:
        assert self.receiver.last_turn
        self.play(color=self.receiver.last_turn.next_color, pos=None)

    def do_last_stone(self) -> None:
        curr = self.last_stone
        while curr:
            try:
                curr = curr.children[0]
            except IndexError:
                break
        self.set_cursor(curr)

    def annotate(self, pos: Pos, name: str | Color | Marker, end: Pos | None = None):
        self.__game.annotate(pos=pos, name=name, end=end)

    def rm_anno(self):
        self.__game.rm_anno()

    def annotate_winrates(self, infos: dict) -> None:
        self.__game.annotate_winrates(infos=infos)

    def set_end_result(self, result_type, color: Color | None = None):
        self.__game.set_end_result(result_type, color)

    def toggle_status(self, pos):
        self.__game.toggle_status(pos)

    def add_receiver(self, receiver: BaseReceiver):
        self.__game.add_receiver(receiver=receiver)

    def add_controller(self, cls: Type[G], force_create=False, **kwargs) -> tuple[G, bool]:
        created = False
        if cls not in self._subs or force_create:
            ctrl = cls(game=self.__game, **kwargs)
            self._subs.add(ctrl)
            created = True
        return ctrl, created

    def quit(self):
        logging.debug("QUIT CONTROLLER %s", self)
        for ctrl in self._subs:
            ctrl.quit()
        self.__game.quit()
