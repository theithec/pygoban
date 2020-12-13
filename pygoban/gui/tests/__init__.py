from PyQt5.QtCore import pyqtSignal, QObject
from pygoban.tests import ControlledGame
from pygoban.gui.gamewindow import GameWindow


class QontrolledGame(QObject, ControlledGame):
    moves_done_signal = pyqtSignal()
    controllercls = GameWindow
    timeout = 1000

    def start(self, qtbot):
        with qtbot.waitSignal(
            self.moves_done_signal, timeout=self.timeout
        ):  # as blocker:
            self.game.start()

    def done(self, player):
        self.callback(self)
        self.moves_done_signal.emit()
