from PyQt5.QtCore import pyqtSignal, QObject
from pygoban.tests import ControlledGame, MockedPlayer
from pygoban.gui.gamewindow import GameWindow, Controller



class MockedGuiPlayer(MockedPlayer):
    def handle_moves_stopped(self):
        self.tests_controller.done(self)


class QontrolledGame(QObject, ControlledGame):
    playercls = MockedGuiPlayer
    controllercls = GameWindow
    moves_done_signal = pyqtSignal()
    timeout = 1000

    def start(self, qtbot):
        with qtbot.waitSignal(
            self.moves_done_signal, timeout=self.timeout
        ):  # as blocker:
            # qtbot.addWidget(self.controller)
            self.game.start()

    def done(self, player):
        self.callback(self)
        self.moves_done_signal.emit()

