from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
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
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QHeaderView,
)

from pygoban.status import BLACK, WHITE
from pygoban.board import MoveResult
from pygoban.move import Move
from pygoban.coords import pos_to_sgf

from . import InputMode, btn_adder
from .filedialog import filename_from_savedialog
from .player import GuiPlayer
from .tree import Tree


class ActionMixin:
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

    def do_pass(self):
        self.controller.callbacks["pass"](self.controller.last_result.next_player)

    def do_resign(self):
        game = self.controller.game
        if not self.controller.timeout or isinstance(
            self.controller.players[game.nextcolor], GuiPlayer
        ):
            self.controller.handle_move(game.nextcolor, "resign")

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

    def do_undo(self):
        self.controller.input_mode = InputMode.PLAY
        if not self.controller.last_result.move.is_root:
            self.controller.handle_move(self.controller.last_result.move.color, "undo")

    def do_prev_move(self):
        self.controller.callbacks["set_cursor"](self.controller.last_result.move.parent)

    def do_next_move(self):
        self.controller.callbacks["set_cursor"](
            list(self.controller.last_result.move.children.values())[0]
        )

    def do_count(self):
        self.controller.input_mode = InputMode.COUNT
        self.controller.count()


class Sidebar(QFrame, ActionMixin):

    timeupdate_signal = pyqtSignal()
    timeended_signal = pyqtSignal()
    game_signal = pyqtSignal(MoveResult)
    moves_signal = pyqtSignal(Move)

    BLACK_STYLE = "QLabel { background-color : black; color : white; }"
    WHITE_STYLE = "QLabel { background-color : white; color : black; }"

    def __init__(self, parent, is_game=True, can_edit=True):
        super().__init__(parent)
        self.controller = parent
        self.is_game = is_game
        self.can_edit = can_edit

        self.setMinimumWidth(180)
        layout = QFormLayout()
        btn_settings = QPushButton("\u2630")
        btn_settings.setMenu(self.get_menu())
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(btn_settings, 0, Qt.AlignRight)
        layout.addRow(settings_layout)
        self.player_controlls = {}
        self.controlls = {}
        self.timer = None
        self.timeupdate_signal.connect(self.update_clock)
        self.timeended_signal.connect(self.time_ended)
        self.game_signal.connect(self.update_controlls)
        self.moves_signal.connect(self.update_moves)

        for color in (BLACK, WHITE):
            curr = {}
            self.player_controlls[color] = curr
            player_box = QGroupBox(str(color))
            player_layout = QFormLayout()
            player_layout.addRow("Name:", QLabel(self.controller.players[color].name))
            curr["prisoners_label"] = QLabel(
                str(self.controller.callbacks["get_prisoners"]()[color])
            )
            player_layout.addRow("Prisoners:", curr["prisoners_label"])
            if self.controller.timesettings:
                curr["time"] = QLCDNumber()
                curr["time"].display(
                    self.controller.players[color].timesettings.nexttime()
                )
                player_layout.addRow(curr["time"])
            player_box.setLayout(player_layout)
            layout.addRow(player_box)

        if is_game:
            layout.addRow(self.get_game_box())

        if can_edit:
            layout.addRow(self.get_edit_box())

        # self.tree = QTreeWidget(self)
        self.tree = Tree(self, self.tree_click)
        # self.tree.itemClicked.connect(self.tree_click)
        # self.tree.setColumnCount(1)
        # self.tree.horizontalScrollBar().setEnabled(True)
        # self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # self.tree.header().setStretchLastSection(False)
        # self.tree_items = {}
        layout.addRow(self.tree)
        self.comments = QTextEdit()
        self.comments.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addRow(self.comments)

        layout.addRow("Ruleset", QLabel(str(self.controller.infos["RU"])))
        self.setLayout(layout)

    def get_game_box(self):
        game_box = QGroupBox("Game")
        game_layout = QHBoxLayout()
        add_gamebutton = btn_adder(game_layout)
        self.undo_btn = add_gamebutton("Undo", self.do_undo)
        self.pass_btn = add_gamebutton("Pass", self.do_pass)
        add_gamebutton("Resign", self.do_resign)
        add_gamebutton("Count", self.do_count)
        game_box.setLayout(game_layout)
        return game_box

    def get_edit_box(self):
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

        edit_box = QGroupBox()
        edit_box.setLayout(box_layout)
        return edit_box

    def update_clock(self):
        if not self.controller.timeout:
            curr_player = self.controller.players[
                self.controller.last_result.next_player
            ]
            if self.controller.timesettings:
                self.set_clock(curr_player.color, curr_player.timesettings.nexttime())

    def clock_tick(self):
        seconds = (
            self.player_controlls[self.controller.last_result.next_player][
                "time"
            ].intValue()
            - 1
        )
        self.player_controlls[self.controller.last_result.next_player]["time"].display(
            str(seconds)
        )

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
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_as_file)
        menu = QMenu(self)
        menu.addAction(save_action)
        menu.addSeparator()
        return menu

    def save_as_file(self):
        name = filename_from_savedialog(self)
        with open(name, "w") as fileobj:
            fileobj.write(self.controller.game.to_sgf())

    def tree_click(self, item, _col=None):
        self.controller.callbacks["set_cursor"](item)

    def update_controlls(self, result):
        print("\nUPDATE CONTL", result)
        for color in (BLACK, WHITE):
            curr = self.player_controlls[color]
            curr["prisoners_label"].setText(
                str(self.controller.callbacks["get_prisoners"]()[color])
            )

        if self.is_game:
            self.pass_btn.setEnabled(
                isinstance(
                    self.controller.players[result.next_player],
                    GuiPlayer,
                )
            )
        if self.can_edit:
            has_parent = bool(result.move and result.move.parent)
            self.prev_move.setEnabled(has_parent)
            self.back_moves.setEnabled(has_parent)

            has_children = bool(result.move and len(result.move.children))
            self.next_move.setEnabled(has_children)
            self.forward_moves.setEnabled(has_children)

        if result.move:
            cmts = result.move.extras.comments or [""]
            self.comments.setText("\n".join(cmts))

            if result.is_new:
                self.tree.add_move(result.move)
            else:
                self.tree.set_cursor(result.move)

        # if key := self.tree_items.get(id(result.move)):
        #    self.tree.setCurrentItem(key[0])

    def update_moves(self, move: Move):
        print("UPDATE MOVE", move)
        self.tree.add_move(move)
        self.tree.canvas.set_moves(move)
        # if (has := len(self.tree_items)) % 100 == 0:
        #     print("u", has, move)
        # if move.parent:
        #     res = self.tree_items.get(id(move.parent))
        #     tree_parent = None
        #     if res:
        #         tree_parent = res[0]
        #     if not tree_parent:
        #         tree_parent = self.tree
        #     item = QTreeWidgetItem(tree_parent)
        #     item.key = id(move)
        #     #item.setText(0, str(move.pos))
        #     label = QLabel()
        #     if move.pos:
        #         mstr = pos_to_sgf(move.pos, self.controller.infos['SZ'])
        #     else:
        #         mstr = "-"
        #     level = len(move.get_path()) - 1
        #     label.setText(f"{level}: {mstr}")
        #     label.setStyleSheet(self.BLACK_STYLE if move.color == BLACK else self.WHITE_STYLE)
        #     self.tree.setItemWidget(item,0, label)
        #     item.setSizeHint(0, label.sizeHint())
        #     self.tree_items[id(move)] = (item, move)
        # for child in move.children.values():
        #     self.update_moves(child)
        # self.tree.expandAll()
