import logging
from typing import Any

from PyQt6.QtCore import QCoreApplication  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
)

from .. import Color, gtp
from . import GUIMode, MainUI

_translate = QCoreApplication.translate


class NewGameBaseDialog(QDialog):
    """Define gamesettings"""

    SHOW_PLAYER_TYPE = False
    GUI_MODE: GUIMode

    def __init__(self, parent: MainUI):
        super().__init__(parent)
        self.manager = parent
        self.init_ui()

    def init_ui(self):  # pylint: disable=invalid-name
        layout = QFormLayout()
        self.for_player = {}

        settings = self.manager.settings
        for color in (Color.BLACK, Color.WHITE):
            colname = str(color)
            self.for_player[color] = {}
            group_box = QGroupBox(colname)
            group_layout = QFormLayout()

            for_player = self.for_player[color]
            if self.SHOW_PLAYER_TYPE:
                for_player["type"] = QComboBox()
                playertypes = ["human", *settings.gtp_engines.keys()]
                for_player["type"].addItems(playertypes)
                group_layout.addRow("Type", for_player["type"])
            for_player["name_edit"] = QLineEdit(
                _translate(
                    "NewGameDialog", getattr(settings, f"{color.name.lower()}_name", colname)
                )
            )
            group_layout.addRow("Name", for_player["name_edit"])
            group_box.setLayout(group_layout)
            layout.addRow(group_box)

        self.size_box = QComboBox()
        self.size_box.addItems(["9", "13", "19"])
        index = self.size_box.findText(str(settings.boardsize))
        self.size_box.setCurrentIndex(index)
        self.ruleset_box = QComboBox()
        self.ruleset_box.addItems(["Edit", "Japanese"])
        self.ruleset_box.setCurrentIndex(1)
        self.komi_edit = QLineEdit("6.5")
        self.handicap_box = QComboBox()
        self.handicap_box.addItems([str(i) for i in range(10)])

        self.time_check = QCheckBox()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.startgame)

        layout.addRow(_translate("NewGameDialog", "Size:"), self.size_box)
        layout.addRow(_translate("NewGameDialog", "Rules:"), self.ruleset_box)
        layout.addRow("Komi:", self.komi_edit)
        layout.addRow("Handicap:", self.handicap_box)

        self.add_rows(layout)

        layout.addRow(ok_button)
        self.setLayout(layout)
        self.setWindowTitle("New Game - Pygoban")
        # self.show()

    def add_rows(self, layout):
        pass

    def startgame(self, timestr: str | None = None):
        data: dict[str, Any] = dict(
            boardsize=int(self.size_box.currentText()),
            komi=float(self.komi_edit.text()),
            handicap=int(self.handicap_box.currentText()),
            black_name=str(self.for_player[Color.BLACK]["name_edit"].text()),
            white_name=self.for_player[Color.WHITE]["name_edit"].text(),
            modestr=self.GUI_MODE.value,
            timestr=timestr,
        )
        controller = self.manager.add_game_from_atomic_values(**data)
        if self.SHOW_PLAYER_TYPE:
            for color in (Color.BLACK, Color.WHITE):
                txt = self.for_player[color]["type"].currentText()
                if txt != "human":
                    cmd = self.manager.settings.gtp_engines[txt]
                    gtpctrl, created = controller.add_controller(
                        cls=gtp.GTPController, cmd_line=cmd, actions=[color], force_create=True
                    )
                    logging.debug("create for %s: %s", color, cmd)
                    if created:
                        assert controller.receiver.last_turn
                        gtpctrl.receive_game_event(controller.receiver.last_turn)
                        controller.add_receiver(gtpctrl)
                        data[color.name.lower() + "_engine"] = txt
                    else:
                        gtpctrl.set_action(color, True)

        self.close()


class NewGameEditDialog(NewGameBaseDialog):
    GUI_MODE = GUIMode.EDIT


class NewGamePlayDialog(NewGameBaseDialog):
    GUI_MODE = GUIMode.PLAY
    SHOW_PLAYER_TYPE = True

    time_edits: dict[str, QLineEdit]

    def set_time_enabled_status(self):
        is_enabled = self.time_check.isChecked()
        for widget in self.time_edits.values():
            widget.setEnabled(is_enabled)

    def init_ui(self):  # pylint: disable=invalid-name
        super().init_ui()
        self.set_time_enabled_status()

    def startgame(self):
        timestr = (
            ":".join([edit.text() for edit in self.time_edits.values()])
            if self.time_check.isChecked()
            else None
        )
        super().startgame(timestr=timestr)

    def add_rows(self, layout):
        time_box = QGroupBox("Clock")
        time_layout = QFormLayout()
        settings = self.manager.settings
        self.time_edits = {
            "Main time": QLineEdit(settings.main_time),
            "Byoyomi Time": QLineEdit(settings.byoyomi_time),
            "Num Byoyomi": QLineEdit(settings.byoyomi_num),
            "Byoyomi Stones": QLineEdit(settings.byoyomi_stones),
        }
        time_layout.addRow("Use Clock", self.time_check)
        for label, widget in self.time_edits.items():
            time_layout.addRow(label, widget)
        time_box.setLayout(time_layout)
        self.time_check.clicked.connect(self.set_time_enabled_status)
        layout.addRow(time_box)
