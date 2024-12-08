from typing import Type

from .game import AbstractCallbacks, Game, Stone
from .receivers import BaseReceiver


class GameController:
    def __init__(self, game: Game) -> None:
        self.ruleset = game.ruleset
        self.callbacks = game.callbacks()
        self.delete_requested = False

    def start(self, receiver=BaseReceiver) -> None:
        self.receiver = receiver  #: BaseReceiver = receiver_cls(controller=self)
        self.callbacks.start([self.receiver])

    @property
    def curr_stone(self) -> Stone:
        return self.receiver.curr_stone

    def do_prev_variation(self) -> None:
        curr = self.curr_stone
        while curr:
            if (not curr.parent) or len(curr.children) > 1:
                break
            curr = curr.parent

        assert self.callbacks
        self.callbacks.set_cursor(curr)

    def do_next_variation(self) -> None:
        curr = self.curr_stone
        while curr:
            if not curr.children or len(curr.children) > 1:
                break
            curr = curr.children[0]
        assert self.callbacks
        self.callbacks.set_cursor(curr)

    def do_prev_stone(self) -> None:
        assert self.curr_stone.parent
        self.callbacks.set_cursor(self.curr_stone.parent)

    def do_next_stone(self) -> None:
        assert self.curr_stone.children
        self.callbacks.set_cursor(self.curr_stone.children[0])

    def do_first_stone(self) -> None:
        self.callbacks.set_cursor(self.curr_stone.root())

    def do_pass(self) -> None:
        self.callbacks.play(color=self.receiver.curr_stone_result.next_color, pos=None)

    def do_last_stone(self) -> None:
        curr = self.curr_stone
        while curr:
            try:
                curr = curr.children[0]
            except IndexError:
                break
        self.callbacks.set_cursor(curr)
