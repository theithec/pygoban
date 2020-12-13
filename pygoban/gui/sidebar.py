# pylint: disable=invalid-name, arguments-differ
# because qt and do_-commands and Box overloading
from copy import copy
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
from pygoban.move import Empty
from pygoban.player import Player
from pygoban.sgf import CR, SQ, TR
from pygoban import InputMode, Result, events, get_argparser
from pygoban.__main__ import startgame



from . import btn_adder, gamewindow
from .filedialog import filename_from_savedialog
from .player import GuiPlayer
from .tree import Tree


class Box(QGroupBox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.controller: "gamewindow.GameWindow" = parent.controller
        self.events = kwargs.pop("events", [])
        self.kwargs = kwargs
        self.init(**kwargs)

    def init(self):
        raise NotImplementedError()


class PlayerBox(Box):
    timeupdate_signal = pyqtSignal()
    timeended_signal = pyqtSignal()
    timer = None
    seconds = None

    def init(self, player: Player):
        self.player = player
        self.setTitle(f"{self.player.color}: {self.player.name} ")
        self.setStyleSheet("""PlayerBox{
            margin-top: 2ex; /* leave space at the top for the title */

            border-color: %s;
            border-width : .5ex;
            border-style: inset;
            border-radius: 5px;
            padding: 1px 18px 1px 3px;

        }""" % ("white" if player.color == WHITE else "black"))
        player_layout = QFormLayout()
        self.prisoners_label = QLabel(
            str(self.controller.callbacks["get_prisoners"]()[player.color])
        )
        player_layout.addRow("Prisoners:", self.prisoners_label)
        if self.controller.timesettings:
            self.clock = QLCDNumber()
            self.seconds = player.timesettings.nexttime()
            self.clock.display(self.seconds_to_str())
            player_layout.addRow(self.clock)

        self.setLayout(player_layout)
        if self.controller.timesettings:
            self.timeended_signal.connect(self.time_ended)
            self.timeupdate_signal.connect(self.update_clock)

    def update_controlls(self, _result):
        self.prisoners_label.setText(
            str(self.controller.callbacks["get_prisoners"]()[self.player.color])
        )

    def seconds_to_str(self):
        seconds = self.seconds
        hours = int(seconds / 360) if seconds >= 360 else 0
        seconds -= hours * 360
        minutes = int(seconds / 60) if seconds >= 60 else 0
        seconds -= minutes * 60
        txt = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return txt

    def set_clock(self, seconds):
        self.seconds = seconds
        self.time_ended()
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.clock.display(self.seconds_to_str())
        self.timer.timeout.connect(self.clock_tick)

    def update_clock(self):
        if self.player.color == self.controller.last_move_result.next_player:
            self.set_clock(self.player.timesettings.nexttime())
        else:
            self.time_ended()

    def time_ended(self):
        if self.timer:
            self.timer.stop()

    def clock_tick(self):
        self.seconds -= 1
        self.clock.display(self.seconds_to_str())


class GameBox(Box):
    def init(self):
        game_layout = QHBoxLayout()
        add_gamebutton = btn_adder(game_layout)
        self.undo_btn = add_gamebutton("Undo", self.do_undo)
        self.pass_btn = add_gamebutton("Pass", self.do_pass)
        self.resign_btn = add_gamebutton("Resign", self.do_resign)
        self.count_btn = add_gamebutton("Count", self.do_count)
        self.setLayout(game_layout)

    def update_controlls(self, result):
        self.pass_btn.setEnabled(
            self.controller.input_mode == InputMode.PLAY
            and ((
                isinstance(result, events.CursorChanged)
                and isinstance(self.controller.players[result.next_player], GuiPlayer))
                or True)
        )
        self.resign_btn.setEnabled(self.controller.input_mode == InputMode.PLAY)
        self.count_btn.setEnabled(self.controller.input_mode == InputMode.COUNT)

    def do_undo(self):
        self.controller.input_mode = InputMode.PLAY
        self.controller.game_callback(
            "play", color=self.controller.last_move_result.next_player, pos=Empty.UNDO
        )

    def do_pass(self):
        self.controller.game_callback(
            "play", self.controller.last_move_result.next_player, pos=Empty.PASS
        )

    def do_resign(self):
        if not self.controller.timeout or isinstance(
            self.controller.players[self.controller.last_move_result.next_player],
            GuiPlayer,
        ):
            self.controller.game_callback(
                "play", self.controller.last_move_result.next_player, Empty.RESIGN
            )

    def do_count(self):

        if self.controller.input_mode == InputMode.PLAY:
            self.controller.input_mode = InputMode.COUNT
        elif self.controller.input_mode == InputMode.COUNT:
            self.controller.input_mode = InputMode.ENDED
        self.controller.game_callback(
            "count",
            is_final=self.controller.input_mode == InputMode.ENDED)


class EditBox(Box):
    def init(self):
        btns_layout = QHBoxLayout()
        add_dirbutton = btn_adder(btns_layout)
        self.back_moves = add_dirbutton("<<", self.do_last_variation)
        self.prev_move = add_dirbutton("<", self.do_prev_move)
        self.next_move = add_dirbutton(">", self.do_next_move)
        self.forward_moves = add_dirbutton(">>", self.do_next_variation)
        self.tree = Tree(self, self.tree_click)

        deco_layout = QHBoxLayout()
        add_decobutton = btn_adder(deco_layout)
        group = QGroupBox("Deco")
        group.setCheckable(True)
        group.setChecked(False)
        group.toggled.connect(self.toggle_deco)
        add_decobutton("B", self.do_B)
        add_decobutton("W", self.do_W)
        add_decobutton(TR, self.do_tr)
        add_decobutton(SQ, self.do_sq)
        add_decobutton(CR, self.do_ci)
        add_decobutton("1", self.do_nr)
        add_decobutton("A", self.do_char)
        group.setLayout(deco_layout)

        box_layout = QFormLayout()
        box_layout.addRow(btns_layout)
        box_layout.addRow(group)
        box_layout.addRow(self.tree)
        self.setLayout(box_layout)

    def update_controlls(self, result):
        has_parent = bool(result.cursor and result.cursor.parent)
        self.prev_move.setEnabled(has_parent)
        self.back_moves.setEnabled(has_parent)
        has_children = (result.cursor and len(result.cursor.children))
        self.next_move.setEnabled(has_children)
        self.forward_moves.setEnabled(has_children)
        if isinstance(result, events.CursorChanged) and not result.cursor.is_root:
            if result.is_new:
                self.tree.add_move(result.cursor)
            else:
                self.tree.set_cursor(result.cursor)

    def tree_click(self, item, _col=None):
        self.controller.callbacks["set_cursor"](item)

    def toggle_deco(self, checked):
        self.controller.input_mode = InputMode.EDIT if checked else InputMode.PLAY

    def do_B(self):
        self.controller.deco = BLACK

    def do_W(self):
        self.controller.deco = WHITE

    def do_tr(self):
        self.controller.deco = TR

    def do_sq(self):
        self.controller.deco = SQ

    def do_ci(self):
        self.controller.deco = CR

    def do_nr(self):
        self.controller.deco = "NR"

    def do_char(self):
        self.controller.deco = "CHAR"

    def do_last_variation(self):
        curr = self.controller.last_move_result.cursor
        while curr:
            if curr.parent and len(curr.parent.children) == 1:
                curr = curr.parent
            else:
                break
        self.controller.callbacks["set_cursor"](curr)

    def do_next_variation(self):
        curr = self.controller.last_move_result.cursor
        while curr:
            if len(curr.children) == 1:
                curr = list(curr.children.values())[0]
            else:
                break
        self.controller.callbacks["set_cursor"](curr)

    def do_prev_move(self):
        self.controller.callbacks["set_cursor"](
            self.controller.last_move_result.cursor.parent
        )

    def do_next_move(self):
        self.controller.callbacks["set_cursor"](
            list(self.controller.last_move_result.cursor.children.values())[0]
        )


class Sidebar(QFrame):

    game_signal = pyqtSignal(events.Event)

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
            self.gamebox = self.add_box(GameBox(self))

        if can_edit:
            self.editbox = self.add_box(EditBox(self, events=[events.CursorChanged, events.Ended]))

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
        newwindow_action = QAction("Open in new window", self)
        newwindow_action.triggered.connect(self.new_open)
        menu.addAction(newwindow_action)
        return menu

    def save_as_file(self):
        name = filename_from_savedialog(self)
        with open(name, "w") as fileobj:
            fileobj.write(self.controller.to_sgf())

    def new_open(self):
        parser = get_argparser()
        args = [None]
        for col in (BLACK, WHITE):
            pname = self.controller.players[col].name
            args.append(f"--{str(col).lower()}-name={pname}")

        for arg, key in (
            ("boardsize", "SZ"),
            ("komi", "KM"),
        ):
            val = self.controller.infos[key]
            args.append(f"--{arg}={val}")
        args.append("--mode=EDIT")
        args = parser.parse_args(args)
        c = startgame(args, init_gui=False, root=copy(self.controller.root))[1]
        c.input_mode = InputMode.PLAY
        c.sidebar.editbox.do_next_variation()

    def update_controlls(self, event):
        self.editbox.setVisible(self.controller.mode == "EDIT")
        self.gamebox.setVisible(self.controller.mode == "PLAY")
        for box in self.boxes:
            if not box.events or event.__class__ in box.events:
                box.update_controlls(event)
        if isinstance(event, events.CursorChanged):
            cmts = event.cursor.extras.comments or [""]
            self.comments.setText("\n".join(cmts))

