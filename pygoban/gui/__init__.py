import os
from PyQt5 import QtWidgets
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CenteredMixin:
    def center(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
