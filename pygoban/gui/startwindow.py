import sys
import argparse
#  from OpenGL import GL  # noqa: F401
from collections import OrderedDict
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import (  # pylint: disable=no-name-in-module
    QCoreApplication)

from pygoban import logging
from . import BASE_DIR, CenteredMixin, newgamedialog

_translate = QCoreApplication.translate


class StartWindow(CenteredMixin, QtWidgets.QFrame):
    '''Define gamesettings'''

    def __init__(self, parser: argparse.ArgumentParser, starter_callback):
        self.parser = parser
        self.starter_callback = starter_callback
        super().__init__()
        self.initUI()

    def initUI(self):  # pylint: disable=invalid-name
        self.setWindowTitle('Pygoban')
        self.setObjectName("StartWindow")
        layout = QtWidgets.QGridLayout()
        innerlayout = QtWidgets.QVBoxLayout()
        innerlayout.setContentsMargins(80, 30, 80, 30)
        self.newgame_button = QtWidgets.QPushButton(self)
        self.newgame_button.setText(_translate("Dialog", "New Game"))
        innerlayout.addWidget(self.newgame_button)
        self.openfile_button = QtWidgets.QPushButton(self)
        self.openfile_button.setSizeIncrement(QtCore.QSize(100, 100))
        self.openfile_button.setFlat(False)
        innerlayout.addWidget(self.openfile_button)
        self.settings_button = QtWidgets.QPushButton(self)
        innerlayout.addWidget(self.settings_button)
        self.help_button = QtWidgets.QPushButton(self)
        innerlayout.addWidget(self.help_button)
        self.setStyleSheet('''
            #StartWindow {
                border-image: url(%s/gui/imgs/go-board-intersections.jpg) 0 0 0 0 stretch stretch;
            }
            #StartWindow QPushButton { padding: 12px; min-width: 160px }
        ''' % BASE_DIR)
        # self.retranslate_ui(self)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.newgame_button.clicked.connect(self.newgamedialog)
        #self.openfile_button.clicked.connect(self.openfile_from_dialog)
        #self.settings_button.clicked.connect(self.settingsdialog)
        layout.setColumnStretch(0, 0)
        layout.addLayout(innerlayout, 1, 0)
        layout.setColumnStretch(2, 0)
        self.setWindowIcon(QtGui.QIcon('gui/imgs/icon.png'))
        self.setLayout(layout)
        self.center()

    def newgamedialog(self):
        #dlg = newgamedialog.NewGameDialog(self)
        #dlg.show()
        self.starter_callback(args=self.parser.parse_args(), init_gui=False)


