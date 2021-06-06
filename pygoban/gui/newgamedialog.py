import argparse
from collections import OrderedDict

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
)

from pygoban import getconfig
from pygoban.status import BLACK, WHITE


_translate = QCoreApplication.translate


class NewGameDialog(QDialog):
    """Define gamesettings"""

    def __init__(self, parent, parser: argparse.ArgumentParser, starter_callback):
        self.parser = parser
        self.starter_callback = starter_callback
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):  # pylint: disable=invalid-name
        layout = QFormLayout()
        self.for_player = {}
        for color in (BLACK, WHITE):
            colname = str(color)
            self.for_player[color] = {}
            group_box = QGroupBox(colname)
            group_layout = QFormLayout()

            for_player = self.for_player[color]
            for_player["conn_box"] = QComboBox()
            playertypes = ["human", *getconfig()["GTP"].keys()]
            for_player["conn_box"].addItems(playertypes)
            for_player["name_edit"] = QLineEdit(_translate("NewGameDialog", colname))
            group_layout.addRow("Type", for_player["conn_box"])
            group_layout.addRow("Name", for_player["name_edit"])
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

        self.time_check = QCheckBox()
        time_box = QGroupBox("Clock")
        time_layout = QFormLayout()
        self.time_edits = OrderedDict(
            (
                ("Main time", QLineEdit("")),
                ("Byoyomi Time", QLineEdit("")),
                ("Num Byoyomi", QLineEdit("")),
                ("Byoyomi Stones", QLineEdit("")),
            )
        )
        time_layout.addRow("Use Clock", self.time_check)
        for label, widget in self.time_edits.items():
            time_layout.addRow(label, widget)
        time_box.setLayout(time_layout)
        self.time_check.clicked.connect(self.set_time_enabled_status)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.startgame)

        layout.addRow(_translate("NewGameDialog", "Size:"), self.size_box)
        layout.addRow(_translate("NewGameDialog", "Rules:"), self.ruleset_box)
        layout.addRow("Komi:", self.komi_edit)
        layout.addRow("Handicap:", self.handicap_box)

        layout.addRow(time_box)
        layout.addRow(ok_button)
        self.setLayout(layout)
        self.setWindowTitle("New Game - Pygoban")
        self.set_time_enabled_status()
        self.show()

    def set_time_enabled_status(self):
        is_enabled = self.time_check.isChecked()
        for widget in self.time_edits.values():
            widget.setEnabled(is_enabled)

    def startgame(self):
        args = [None]
        for col in (BLACK, WHITE):
            ptype = self.for_player[col]["conn_box"].currentText()
            if ptype != "human":
                args.append(f"--{str(col).lower()}-gtp={ptype}")
            pname = self.for_player[col]["name_edit"].text()
            args.append(f"--{str(col).lower()}-name={pname}")
        for arg, box in (
            ("boardsize", self.size_box),
            ("handicap", self.handicap_box),
        ):
            args.append(f"--{arg}=" + box.currentText())
        args.append(f"--komi=" + self.komi_edit.text())
        if self.time_check.isChecked():
            timestr = ":".join([edit.text() for edit in self.time_edits.values()])
            args.append(f"--time=" + timestr)
        args = self.parser.parse_args(args)
        self.starter_callback(**vars(args), init_gui=False)
        self.close()
