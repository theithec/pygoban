# pylint: disable=invalid-name, arguments-differ
# because qt and do_-commands and Box overloading
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QAction,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTextEdit,
)

from pygoban.status import BLACK, WHITE
from pygoban.board import MoveResult
from pygoban.player import Player

from . import InputMode, btn_adder
from .filedialog import filename_from_savedialog
from .player import GuiPlayer
from .tree import Tree


class Box(QGroupBox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.controller = parent.controller
        self.kwargs = kwargs
        self.init(**kwargs)

    def init(self):
        raise NotImplementedError()


class PlayerBox(Box):
    timeupdate_signal = pyqtSignal()
    timeended_signal = pyqtSignal()
    timer = None

    def init(self, player: Player):
        self.player = player
        player_layout = QFormLayout()
        player_layout.addRow("Name:", QLabel(self.player.name))
        self.prisoners_label = QLabel(
            str(self.controller.callbacks["get_prisoners"]()[player.color])
        )
        player_layout.addRow("Prisoners:", self.prisoners_label)
        if self.controller.timesettings:
            self.clock = QLCDNumber()
            self.clock.display(player.timesettings.nexttime())
            player_layout.addRow(self.clock)
        self.setLayout(player_layout)
        if self.controller.timesettings:
            self.timeended_signal.connect(self.time_ended)
            self.timeupdate_signal.connect(self.update_clock)

    def update_controlls(self, _result):
        self.prisoners_label.setText(
            str(self.controller.callbacks["get_prisoners"]()[self.player.color])
        )

    def set_clock(self, seconds):
        self.time_ended()
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.clock.display(seconds)
        self.timer.timeout.connect(self.clock_tick)

    def update_clock(self):
        if self.player.color == self.controller.last_result.next_player:
            self.set_clock(self.player.timesettings.nexttime())
        else:
            self.time_ended()

    def time_ended(self):
        if self.timer:
            self.timer.stop()

    def clock_tick(self):
        seconds = self.clock.intValue() - 1
        self.clock.display(str(seconds))


class GameBox(Box):
    def init(self):
        game_layout = QHBoxLayout()
        add_gamebutton = btn_adder(game_layout)
        self.undo_btn = add_gamebutton("Undo", self.do_undo)
        self.pass_btn = add_gamebutton("Pass", self.do_pass)
        add_gamebutton("Resign", self.do_resign)
        add_gamebutton("Count", self.do_count)
        self.setLayout(game_layout)

    def update_controlls(self, result):
        self.pass_btn.setEnabled(
            isinstance(
                self.controller.players[result.next_player],
                GuiPlayer,
            )
        )

    def do_undo(self):
        self.controller.input_mode = InputMode.PLAY
        if not self.controller.last_result.move.is_root:
            self.controller.handle_move(self.controller.last_result.move.color, "undo")

    def do_pass(self):
        self.controller.callbacks["pass"](self.controller.last_result.next_player)

    def do_resign(self):
        game = self.controller.game
        if not self.controller.timeout or isinstance(
            self.controller.players[game.nextcolor], GuiPlayer
        ):
            self.controller.handle_move(game.nextcolor, "resign")

    def do_count(self):
        self.controller.input_mode = InputMode.COUNT
        self.controller.count()


class EditBox(Box):
    def init(self):
        btns_layout = QHBoxLayout()
        add_dirbutton = btn_adder(btns_layout)
        self.back_moves = add_dirbutton("<<", self.do_last_variation)
        self.prev_move = add_dirbutton("<", self.do_prev_move)
        self.next_move = add_dirbutton(">", self.do_next_move)
        self.forward_moves = add_dirbutton(">>", self.do_next_variation)

        deco_layout = QHBoxLayout()
        add_decobutton = btn_adder(deco_layout)
        group = QGroupBox("Deco")
        group.setCheckable(True)
        group.setChecked(False)
        group.toggled.connect(self.toggle_deco)
        add_decobutton("B", self.do_B)
        add_decobutton("W", self.do_W)
        add_decobutton("▲", self.do_tr)
        add_decobutton("■", self.do_sq)
        add_decobutton("●", self.do_ci)
        add_decobutton("1", self.do_nr)
        add_decobutton("A", self.do_char)
        group.setLayout(deco_layout)

        box_layout = QFormLayout()
        box_layout.addRow(btns_layout)
        box_layout.addRow(group)

        self.setLayout(box_layout)

    def update_controlls(self, result):
        has_parent = bool(result.move and result.move.parent)
        self.prev_move.setEnabled(has_parent)
        self.back_moves.setEnabled(has_parent)

        has_children = bool(result.move and len(result.move.children))
        self.next_move.setEnabled(has_children)
        self.forward_moves.setEnabled(has_children)

    def toggle_deco(self, checked):
        self.controller.input_mode = InputMode.EDIT if checked else InputMode.PLAY

    def do_B(self):
        self.controller.deco = BLACK

    def do_W(self):
        self.controller.deco = WHITE

    def do_tr(self):
        self.controller.deco = "▲"

    def do_sq(self):
        self.controller.deco = "■"

    def do_ci(self):
        self.controller.deco = "●"

    def do_nr(self):
        self.controller.deco = "NR"

    def do_char(self):
        self.controller.deco = "CHAR"

    def do_last_variation(self):
        curr = self.controller.last_result.move
        while curr:
            if curr.parent and len(curr.parent.children) == 1:
                curr = curr.parent
            else:
                break
        self.controller.callbacks["set_cursor"](curr)

    def do_next_variation(self):
        curr = self.controller.last_result.move
        while curr:
            if len(curr.children) == 1:
                curr = list(curr.children.values())[0]
            else:
                break
        self.controller.callbacks["set_cursor"](curr)

    def do_prev_move(self):
        self.controller.callbacks["set_cursor"](self.controller.last_result.move.parent)

    def do_next_move(self):
        self.controller.callbacks["set_cursor"](
            list(self.controller.last_result.move.children.values())[0]
        )


class Sidebar(QFrame):

    game_signal = pyqtSignal(MoveResult)

    BLACK_STYLE = "QLabel { background-color : black; color : white; }"
    WHITE_STYLE = "QLabel { background-color : white; color : black; }"

    def __init__(self, parent, is_game=True, can_edit=True):
        super().__init__(parent)
        self.controller = parent
        self.setMinimumWidth(180)
        self.layout = QFormLayout()
        btn_settings = QPushButton("\u2630")
        btn_settings.setMenu(self.get_menu())
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(btn_settings, 0, Qt.AlignRight)
        self.layout.addRow(settings_layout)
        self.boxes = []
        self.controls = {}
        self.game_signal.connect(self.update_controlls)

        for color in (BLACK, WHITE):
            self.controls[color] = self.add_box(
                PlayerBox(self, player=self.controller.players[color])
            )

        if is_game:
            self.add_box(GameBox(self))

        if can_edit:
            self.layout.addRow(EditBox(self))

        self.tree = Tree(self, self.tree_click)
        self.layout.addRow(self.tree)
        self.comments = QTextEdit()
        self.comments.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addRow(self.comments)

        self.layout.addRow("Ruleset", QLabel(str(self.controller.infos["RU"])))
        self.setLayout(self.layout)

    def add_box(self, box):
        self.boxes.append(box)
        self.layout.addRow(box)
        return box

    def get_menu(self):
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_as_file)
        menu = QMenu(self)
        menu.addAction(save_action)
        menu.addSeparator()
        return menu

    def save_as_file(self):
        name = filename_from_savedialog(self)
        with open(name, "w") as fileobj:
            fileobj.write(self.controller.to_sgf())

    def tree_click(self, item, _col=None):
        self.controller.callbacks["set_cursor"](item)

    def update_controlls(self, result):
        for box in self.boxes:
            box.update_controlls(result)

        if result.move:
            cmts = result.move.extras.comments or [""]
            self.comments.setText("\n".join(cmts))

            if result.is_new:
                self.tree.add_move(result.move)
            else:
                self.tree.set_cursor(result.move)
