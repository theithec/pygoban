from collections import defaultdict

from PyQt6.QtCore import QCoreApplication  # pylint: disable=no-name-in-module
from PyQt6.QtCore import QSettings  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pygoban import Settings

from . import CenteredMixin
from pygoban import gtp

_translate = QCoreApplication.translate


class SettingsDialog(QDialog, CenteredMixin):
    """Define gamesettings"""

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.settings: Settings = parent.settings
        self.elems: dict[str, QComboBox | QLineEdit | QCheckBox] = {}
        self.qsettings = QSettings("theithec", "pygoban")
        self.widgets = defaultdict((lambda: QLineEdit), boardsize=QComboBox)  # type: ignore
        self.gtp_fields_list: list[tuple[QLineEdit, QLineEdit]] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.add_tab(_translate("SettingsDialog", "Defaults"), self.get_gamelayout())
        self.add_tab(_translate("SettingsDialog", "Player"), self.get_playerlayout())
        self.add_tab(_translate("SettingsDialog", "Clock"), self.get_timelayout())
        self.add_tab(_translate("SettingsDialog", "Engines"), self.get_gtplayout())
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.save)
        layout.addWidget(self.tabs)
        layout.addWidget(ok_button)

        self.setLayout(layout)
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle(_translate("SettingsDialog", "Pygoban Settings"))
        # self.exec_()

    def add_tab(self, name, layout):
        widget = QWidget()
        widget.setLayout(layout)
        self.tabs.addTab(widget, name)

    def add_row(self, layout, name, widget):
        setting = getattr(self.settings, name)
        if widget is None:
            widget = QLineEdit()
            widget.setText(str(setting))
        layout.addRow(name, widget)

        self.elems[name] = widget

    def get_gamelayout(self):
        layout = QFormLayout()

        for name in (
            "boardsize",
            "komi",
            "handicap",
        ):
            widget = None
            if name == "boardsize":
                widget = QComboBox()
            self.add_row(layout, name, widget)

        sizewidget = self.elems["boardsize"]
        assert isinstance(sizewidget, QComboBox)
        sizewidget.addItems(("5", "9", "13", "19"))
        index = sizewidget.findText(str(self.settings.boardsize))
        sizewidget.setCurrentIndex(index)
        return layout

    def get_timelayout(self):
        layout = QFormLayout()

        names = (
            "main_time",
            "byoyomi_time",
            "byoyomi_num",
            "byoyomi_stones",
        )
        for name in names:
            self.add_row(layout, name, None)
            self.elems[name].setText(str(getattr(self.settings, name)))

        return layout

    def get_playerlayout(self):
        layout = QFormLayout()

        for name in (
            "min_wait",
            "auto_save",
        ):
            if name == "auto_save":
                widget = QCheckBox()
            else:
                widget = None
            self.add_row(layout, name, widget)

        autowidget = self.elems["auto_save"]
        assert isinstance(autowidget, QCheckBox)
        # autowidget.setChecked(bool(self.settings.get("auto_save")))
        return layout

    def get_gtplayout3(self):
        items = list(self.settings.gtp_engines.items())
        # items = (("kata", "/bin/katago"), ("gnugo", "/usr/games/gnugo"))

        def mk_handler(index):
            def handler(*args, **kwargs):
                print("check ", items[index], args, kwargs)
                process = gtp.get_process(items[index][1])
                gtp.do_cmd("help", process)
                nextline = process.stdout.readline().decode().strip()
                print("gtp:", nextline)

            return handler

        layout = QGridLayout()
        items = list(self.settings.gtp_engines.items()) + [("", "")]
        # items = (("kata", "/bin/katago"), ("gnugo", "/usr/games/gnugo"))
        for index, (name, cmd) in enumerate(items):
            label = QLabel(name)
            label.setMinimumWidth(80)
            layout.addWidget(label, index, 0)
            gtp_nameedit = QLineEdit(name)
            gtp_nameedit.setMinimumWidth(80)
            gtp_nameedit.setMaximumWidth(80)
            layout.addWidget(gtp_nameedit, index, 1)
            gtp_cmdedit = QLineEdit(cmd)
            layout.addWidget(gtp_cmdedit, index, 2)
            gtp_btn_check = QPushButton("Check")
            gtp_btn_check.clicked.connect(mk_handler(index))
            layout.addWidget(gtp_btn_check, index, 3)
        return layout

    def get_gtplayout(self):
        layout = QVBoxLayout()
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Name"))
        label_layout.addWidget(QLabel("Command"))
        labels = QWidget()
        labels.setLayout(label_layout)
        layout.addWidget((labels))

        items = list(self.settings.gtp_engines.items())
        items.append(("", ""))

        for name, cmd in items:
            gtp_group = QGroupBox(name or "New")
            gtp_group_layout = QHBoxLayout()
            gtp_nameedit = QLineEdit(name)
            gtp_cmdedit = QLineEdit(cmd)
            self.gtp_fields_list.append((gtp_nameedit, gtp_cmdedit))
            gtp_group_layout.addWidget(gtp_nameedit)
            gtp_group_layout.addWidget(gtp_cmdedit)
            gtp_group.setLayout(gtp_group_layout)
            layout.addWidget(gtp_group)
        return layout

    def save(self):
        handled = self.elems.copy()
        gtp_engines = {}
        for fields in self.gtp_fields_list:
            name = fields[0].text()
            if name:
                gtp_engines[name] = fields[1].text()
        self.qsettings.setValue("gtp/engines", gtp_engines)
        self.settings.gtp_engines = gtp_engines

        full_names = {
            "boardsize": "board/size",
            "komi": "board/komi",
            "handicap": "board/handicap",
            "main_time": "clock/main_time",
            "byoyomi_num": "clock/byoyomi_num",
            "byoyomi_time": "clock/byoyomi_time",
            "byoyomi_stones": "clock/byoyomi_stones",
            # "gtp_engines": "gtp/engines",
        }
        for name, widget in handled.items():
            if isinstance(widget, QComboBox):
                val = widget.currentText()
            else:
                val = widget.text()
            full_name = full_names.get(name, name)
            self.qsettings.setValue(full_name, val)
            setattr(self.settings, name, val)
            print("SET", name, full_name, val)
        print("SAVE", self.qsettings.value("gtp/engines"))
        self.qsettings.sync()
        self.accept()
