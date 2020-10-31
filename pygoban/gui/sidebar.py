from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QAction, QFileDialog, QFormLayout, QFrame,
                             QGroupBox, QHBoxLayout, QLabel,
                             QLCDNumber, QMenu, QPushButton, QSizePolicy,
                             QTextEdit)

from pygoban.status import BLACK, WHITE
from . import InputMode, btn_adder
from .intersection import Intersection
from .player import GuiPlayer
from .filedialog import filename_from_savedialog


class Sidebar(QFrame):

    timeupdate_signal = pyqtSignal()
    timeended_signal = pyqtSignal()
    game_signal = pyqtSignal(str)

    def __init__(self, parent, is_game=True, can_edit=True):
        super().__init__(parent)
        self.controller = parent
        self.is_game = is_game
        self.can_edit = can_edit

        self.setGeometry(0, 0, 180, parent.height())
        self.setMinimumSize(80, 30)

        layout = QFormLayout()
        btn_settings = QPushButton('\u2630')
        btn_settings.setMenu(self.get_menu())
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(btn_settings, 0, Qt.AlignRight)
        layout.addRow(settings_layout)
        self.player_controlls = {}
        self.controlls = {}
        self.timer = None
        self.timeupdate_signal.connect(self.update_clock)
        self.timeended_signal.connect(self.time_ended)
        self.game_signal.connect(self.game_update)

        for color in (BLACK, WHITE):
            curr = {}
            self.player_controlls[color] = curr
            player_box = QGroupBox(str(color))
            player_layout = QFormLayout()
            player_layout.addRow("Name:", QLabel(self.controller.players[color].name))
            curr['prisoners_label'] = QLabel(str(self.controller.game.prisoners[color]))
            player_layout.addRow("Prisoners:", curr['prisoners_label'])
            if self.controller.timesettings:
                curr['time'] = QLCDNumber()
                curr['time'].display("00:00")
                player_layout.addRow(curr['time'])
            player_box.setLayout(player_layout)
            layout.addRow(player_box)

        if is_game:
            layout.addRow(self.get_game_box())

        if can_edit:
            layout.addRow(self.get_edit_box())

        self.comments = QTextEdit()
        self.comments.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addRow(self.comments)

        layout.addRow("Ruleset", QLabel(str(self.controller.game.ruleset.name)))
        self.setLayout(layout)

    def get_game_box(self):
        self.pass_btn = QPushButton("Pass")
        self.pass_btn.clicked.connect(self.do_pass)
        resign_btn = QPushButton("Resign")
        resign_btn.clicked.connect(self.do_resign)
        game_box = QGroupBox("Game")
        game_layout = QHBoxLayout()
        game_layout.addWidget(self.pass_btn)
        game_layout.addWidget(resign_btn)
        game_box.setLayout(game_layout)
        return game_box

    def get_edit_box(self):
        btns_layout = QHBoxLayout()
        add_dirbutton = btn_adder(btns_layout)
        self.back_moves = add_dirbutton("<<", self.do_back)
        self.prev_move = add_dirbutton("<", self.do_undo)
        self.next_move = add_dirbutton(">", self.do_redo)
        self.forward_moves = add_dirbutton(">>", self.do_next)
        self.foo = add_dirbutton("mark", self.do_mark)
        edit_box = QGroupBox()
        edit_box.setLayout(btns_layout)
        return edit_box

    def do_mark(self):
        self.controller.input_mode = (
            InputMode.EDIT if self.controller.input_mode == InputMode.PLAY else InputMode.PLAY)

    def do_pass(self):
        game = self.controller.game
        self.controller.handle_move(game.currentcolor, "pass")

    def do_resign(self):
        game = self.controller.game
        if not self.controller.timeout or not isinstance(
                self.controller.players[game.currentcolor], GuiPlayer):
            return
        self.controller.handle_move(game.currentcolor, "resign")

    def do_back(self):
        pass

    def do_undo(self):
        movetree = self.controller.game
        if movetree.cursor.is_root:
            return
        self.controller.handle_move(self.controller.game.currentcolor, "undo")
        self.controller.update_board()

    def do_redo(self):
        game = self.controller.game
        move  = list(game.cursor.children.values())[0][0]
        print("Move...", game.cursor.children)
        game._set_cursor(move)
        self.controller.update_board()

    def do_next(self):
        pass

    def game_update(self, txt):
        self.comments.setText(txt)
        # self.update_controls()

    def update_clock(self):
        if not self.controller.timeout:
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

    def save_as_file(self):
        name = filename_from_savedialog(self)
        with open(name, "w") as fileobj:
            fileobj.write(self.controller.game.to_sgf())
        print(name)

    def update_controlls(self):
        for color in (BLACK, WHITE):
            curr = self.player_controlls[color]
            curr['prisoners_label'].setText(str(self.controller.game.prisoners[color]))
        if self.is_game:
            self.pass_btn.setEnabled(
                isinstance(self.controller.players[self.controller.game.currentcolor], GuiPlayer))
        if self.can_edit:
            self.prev_move.setEnabled(bool(
                self.controller.game.cursor and self.controller.game.cursor.parent))
            print("UC", self.controller.game.cursor, self.controller.game.cursor.children)
            self.next_move.setEnabled(bool(self.controller.game.cursor and len(self.controller.game.cursor.children)))
