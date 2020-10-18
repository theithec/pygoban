import argparse
#  from OpenGL import GL  # noqa: F401
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import (  # pylint: disable=no-name-in-module
    QCoreApplication)

from . import BASE_DIR, CenteredMixin, newgamedialog, btn_adder
from .filedialog import filename_from_opendialog

_translate = QCoreApplication.translate


class StartWindow(CenteredMixin, QtWidgets.QFrame):
    '''Define gamesettings'''

    def __init__(self, parser: argparse.ArgumentParser, starter_callback):
        self.parser = parser
        self.starter_callback = starter_callback
        super().__init__()
        self.init_ui()

    def init_ui(self):  # pylint: disable=invalid-name
        self.setWindowTitle('Pygoban')
        self.setObjectName("StartWindow")
        layout = QtWidgets.QGridLayout()
        innerlayout = QtWidgets.QVBoxLayout()
        add_btn = btn_adder(innerlayout)
        innerlayout.setContentsMargins(80, 30, 80, 30)
        self.newgame_button = add_btn(_translate("Dialog", "New Game"), self.newgamedialog)
        self.openfile_button = add_btn(_translate("Dialog", "Open File"), self.open_file)
        self.settings_button = add_btn(_translate("Dialog", "Settings"), self.settingsdialog)
        self.setStyleSheet('''
            #StartWindow {
                border-image: url(%s/gui/imgs/go-board-intersections.jpg) 0 0 0 0 stretch stretch;
            }
            #StartWindow QPushButton {
                padding: 12px; margin: 10px 5px; min-width: 160px
            }
        ''' % BASE_DIR)
        # self.retranslate_ui(self)
        QtCore.QMetaObject.connectSlotsByName(self)
        # self.openfile_button.clicked.connect(self.openfile_from_dialog)
        layout.setColumnStretch(0, 0)
        layout.addLayout(innerlayout, 1, 0)
        layout.setColumnStretch(2, 0)
        self.setWindowIcon(QtGui.QIcon(f'{BASE_DIR}/gui/imgs/icon.png'))
        self.setLayout(layout)
        self.center()

    def newgamedialog(self):
        dlg = newgamedialog.NewGameDialog(self, self.parser, self.starter_callback)
        dlg.show()

    def settingsdialog(self):
        pass

    def open_file(self):
        if filename := filename_from_opendialog(self):
            args = self.parser.parse_args([filename])
            self.starter_callback(args, init_gui=False)
