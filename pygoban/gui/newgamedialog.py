from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QApplication, QComboBox, QPushButton,
    QGroupBox)

from PyQt5.QtCore import (QCoreApplication)

from pygoban.status import BLACK, WHITE



_translate = QCoreApplication.translate


class NewGameDialog(QDialog):
    '''Define gamesettings'''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):  # pylint: disable=invalid-name
        '''init?'''
        layout = QFormLayout()
        self.for_player = {}
        for color in (BLACK, WHITE):
            colname = str(color)
            self.for_player[color] = {}
            group_box = QGroupBox(colname)
            group_layout = QFormLayout()

            for_player = self.for_player[color]
            for_player['conn_box'] = QComboBox()
            for_player['conn_box'].addItems(["A", "B"])
            #for_player['conn_box'].addItems(self.conn_dict.keys())
            #for_player['conn_box'].currentIndexChanged.connect(
            #    getattr(self, "update_%s" % STRSTATUS[color]))
            for_player['name_edit'] = QLineEdit(_translate("NewGameDialog",colname))
            group_layout.addRow('Type', for_player['conn_box'])
            group_layout.addRow('Name', for_player['name_edit'])
            group_box.setLayout(group_layout)
            layout.addRow(group_box)

        self.size_box = QComboBox()
        self.size_box.addItems(["9", "13", "19"])
        self.size_box.setCurrentIndex(2)
        self.ruleset_box = QComboBox()
        self.ruleset_box.addItems(["Edit", "Japanese"])
        self.ruleset_box.setCurrentIndex(1)
        self.komi_edit = QLineEdit("6.5")
        self.handicap_box = QComboBox()
        self.handicap_box.addItems([str(i) for i in range(10)])

        self.maintime_edit = QLineEdit("")
        self.byoyomi_box = QComboBox()
        self.byoyomi_box.addItems(["None", "Japanese"])
        self.byoyomi_edit = QLineEdit(colname)

        ok_button = QPushButton("OK")
        # ok_button.clicked.connect(self.open_board)

        layout.addRow(_translate("NewGameDialog", "Size:"), self.size_box)
        layout.addRow(_translate("NewGameDialog", "Rules:"), self.ruleset_box)
        layout.addRow("Komi:", self.komi_edit)
        layout.addRow("Handicap:", self.handicap_box)
        layout.addRow("Time:", self.maintime_edit)
        layout.addRow("Byoyomi:", self.byoyomi_box)
        layout.addRow("Byoyomi (Seconds):", self.byoyomi_edit)
        layout.addRow(ok_button)

        self.setLayout(layout)
        self.setWindowTitle('New Game - Pygoban')
        self.show()
