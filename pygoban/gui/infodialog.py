from PyQt6.QtCore import Qt  # , pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtGui import QAction  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from pygoban.rulesets import BaseRuleset


class InfoWidget(QWidget):
    def __init__(self, ruleset):
        super().__init__()
        layout = QFormLayout()
        for col, name in ruleset.info.names.items():
            txt = name
            if rank := ruleset.info.ranks.get(col):
                txt += f" {rank}"
            layout.addRow(col.name.capitalize() + ":", QLabel(txt))

        fields = ("boardsize", "komi", "handicap")
        for field in fields:
            layout.addRow(
                field.capitalize() + ":", QLabel(str(getattr(ruleset, field)))
            )

        layout.addRow("Ruleset", QLabel(ruleset.info.ruleset))
        layout.addRow("Result", QLabel(ruleset.info.result))
        self.setLayout(layout)


class InfoDialog(QDialog):
    def __init__(self, ruleset: BaseRuleset):
        super().__init__()

        self.setWindowTitle("Info")

        QBtn = (
            QDialogButtonBox.StandardButton.Ok  # | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(InfoWidget(ruleset))
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.adjustSize()
