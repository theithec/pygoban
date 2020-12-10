from PyQt5.QtCore import pyqtSignal, QObject
from pygoban.tests import MockedPlayer, ControlledGame


class QTestPlayer(QObject, MockedPlayer):
    moves_done_signal = pyqtSignal()

    def handle_game_event(self, event):
        super().handle_game_event(event)
        self.moves_done_signal.emit()


class QontrolledGame(ControlledGame):
    playercls = QTestPlayer
