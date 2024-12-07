from typing import Type

from .game import AbstractCallbacks, Game
from .receivers import BaseReceiver


class GameController:
    def __init__(self, game: Game, receiver_cls: Type[BaseReceiver]) -> None:
        self.ruleset = game.ruleset
        self.receiver: BaseReceiver = receiver_cls()
        self.callbacks: AbstractCallbacks | None = None
        self.callbacks = game.callbacks()
        self.delete_requested = False

    def start(self):
        self.callbacks.start([self.receiver])

    # def __del__(self):
    #    if not self.delete_requested:
    #        self.delete_requested = True
    #        self.receiver.callbacks.finish()
