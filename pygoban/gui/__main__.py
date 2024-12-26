import sys
from PyQt6.QtWidgets import QApplication  # pylint: disable=no-name-in-module


from .mainwindow import MainWindow
from . import merged_config

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config = merged_config()
    mainwin = MainWindow(config=config)
    mainwin.show()

    # Start the event loop.
    app.exec()
