
from PyQt6.QtCore import (  # pylint: disable=no-name-in-module
    QCoreApplication,
    QMetaObject,
)
from PyQt6.QtGui import QIcon  # pylint: disable=no-name-in-module

#  from OpenGL import GL  # noqa: F401
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QFrame,
    QGridLayout,
    QVBoxLayout,
)

from . import BASE_DIR, CenteredMixin, MainUI, btn_adder
from .filedialog import filename_from_opendialog

_translate = QCoreApplication.translate


class StartWidget(CenteredMixin, QFrame):
    def __init__(self, manager: MainUI):
        self.manager = manager
        super().__init__(parent=None)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Pygoban")
        self.setObjectName("StartWindow")
        css = (
            """
            #StartWindow {
                border-image: url(%s/gui/imgs/go-board-intersections.jpg) 0 0 0 0 stretch stretch;
            }
            #StartWindow QPushButton {
                padding: 12px; margin: 10px 5px; min-width: 160px
            }
        """
            % BASE_DIR
        )
        self.setStyleSheet(css)
        layout = QGridLayout()
        innerlayout = QVBoxLayout()
        add_btn = btn_adder(innerlayout)
        innerlayout.setContentsMargins(80, 30, 80, 30)
        self.newgameplay_button = add_btn(
            _translate("Dialog", "Play Game"), self.manager.show_add_game_dialog
        )

        self.newgameedit = add_btn(
            _translate("Dialog", "Edit Board"), self.manager.show_edit_board_dialog
        )
        self.openfile_button = add_btn(
            _translate("Dialog", "Open File"), self.open_file
        )
        self.settings_button = add_btn(
            _translate("Dialog", "Settings"), self.manager.show_settings_dialog
        )
        QMetaObject.connectSlotsByName(self)
        layout.setColumnStretch(0, 0)
        layout.addLayout(innerlayout, 1, 0)
        layout.setColumnStretch(2, 0)
        self.setWindowIcon(QIcon(f"{BASE_DIR}/gui/imgs/icon.png"))
        self.setLayout(layout)
        self.center()

    def open_file(self):
        if filename := filename_from_opendialog(self):
            self.manager.load_sgf(filename)
