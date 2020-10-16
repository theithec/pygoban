from pygoban.status import BLACK, WHITE
from PyQt5.QtCore import (Qt,  QTimer,
                          pyqtSignal)
from PyQt5.QtWidgets import (QAction, QFileDialog, QFormLayout, QFrame,
                             QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLCDNumber, QMenu, QPushButton, QRadioButton,
                             QSizePolicy, QStackedLayout, QTextEdit)


class Sidebar(QFrame):

    timeupdate_signal = pyqtSignal()
    timeended_signal = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.controller = parent

        self.setGeometry(0, 0, 180, parent.height())
        self.setMinimumSize(80, 30)

        layout = QFormLayout()
        btn_settings = QPushButton('\u2630')
        btn_settings.setMenu(self.get_menu())
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(btn_settings, 0, Qt.AlignRight)
        layout.addRow(settings_layout)
        self.player_controlls = {}
        self.timer = None
        self.timeupdate_signal.connect(self.update_clock)
        self.timeended_signal.connect(self.time_ended)

        for color in (BLACK, WHITE):
            curr = {}
            self.player_controlls[color] = curr
            player_box = QGroupBox(str(color))
            player_layout = QFormLayout()
            player_layout.addRow(QLabel(self.controller.players[color].name))
            curr['prisoners_label'] = QLabel(str(self.controller.game.movetree.prisoners[color]))
            curr['time'] = QLCDNumber()
            curr['time'].display("00:00")
            player_layout.addRow(curr['prisoners_label'])
            player_layout.addRow(curr['time'])
            player_box.setLayout(player_layout)
            layout.addRow(player_box)

        layout.addRow("Ruleset", QLabel(str(self.controller.game.ruleset.name)))
        self.setLayout(layout)

    def update_clock(self):
        if self.controller.game.currentcolor:
            curr_player = self.controller.players[self.controller.game.currentcolor]
            if self.controller.players[self.controller.game.currentcolor].timesettings:
                self.set_clock(curr_player.color, curr_player.timesettings.nexttime())

    def clock_tick(self):
        seconds = self.player_controlls[self.controller.game.currentcolor]["time"].intValue() - 1
        self.player_controlls[self.controller.game.currentcolor]["time"].display(str(seconds))

    def set_clock(self, color, seconds):
        self.time_ended()
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.player_controlls[color]["time"].display(seconds)
        self.timer.timeout.connect(self.clock_tick)

    def time_ended(self):
        if self.timer:
            self.timer.stop()

    def get_menu(self):
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_as_file)
        menu = QMenu(self)
        menu.addAction(save_action)
        menu.addSeparator()
        return menu

    def show_menu(self):
        menu = self.get_menu()
        menu.exec_(
            self.controls['settings'].mapToGlobal(
                self.controls['settings'].pos()))

    def save_as_file(self):
        pass

    def update_controlls(self):
        for color in (BLACK, WHITE):
            curr = self.player_controlls[color]
            curr['prisoners_label'].setText(str(self.controller.game.movetree.prisoners[color]))
