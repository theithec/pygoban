import sys

from PyQt6.QtWidgets import QApplication  # pylint: disable=no-name-in-module

from . import merged_config
from .mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config = merged_config()
    mainwin = MainWindow(config=config)
    mainwin.show()
    app.exec()
