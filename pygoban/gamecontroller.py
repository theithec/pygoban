from .game import Game, Node
from .receivers import BaseReceiver


class GameController:
    def __init__(self, game: Game) -> None:
        self.ruleset = game.ruleset
        self.callbacks = game.callbacks()
        self.delete_requested = False

    def start(self, receiver: BaseReceiver, node: Node | None = None) -> None:
        self.receiver = receiver  #: BaseReceiver = receiver_cls(controller=self)
        self.callbacks.start([self.receiver], node=node)

    @property
    def last_stone(self) -> Node:
        assert self.receiver.last_turn
        return self.receiver.last_turn.node

    def do_prev_variation(self) -> None:
        curr = self.last_stone
        while curr:
            if (not curr.parent) or len(curr.children) > 1:
                break
            curr = curr.parent
        self.callbacks.set_cursor(curr)

    def do_next_variation(self) -> None:
        curr = self.last_stone
        while curr:
            if not curr.children or len(curr.children) > 1:
                break
            curr = curr.children[0]
        self.callbacks.set_cursor(curr)

    def do_prev_stone(self) -> None:
        assert self.last_stone and self.last_stone.parent
        self.callbacks.set_cursor(self.last_stone.parent)

    def do_next_stone(self) -> None:
        self.callbacks.set_cursor(self.last_stone.children[0])

    def do_first_stone(self) -> None:
        self.callbacks.set_cursor(self.last_stone.root())

    def do_pass(self) -> None:
        assert self.receiver.last_turn
        self.callbacks.play(color=self.receiver.last_turn.next_color, pos=None)

    def do_last_stone(self) -> None:
        curr = self.last_stone
        while curr:
            try:
                curr = curr.children[0]
            except IndexError:
                break
        self.callbacks.set_cursor(curr)
