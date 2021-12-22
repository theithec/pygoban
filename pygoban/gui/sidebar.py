# pylint: disable=invalid-name, arguments-differ
# because qt and do_-commands and Box overloading
from copy import copy
from typing import Any, Optional

from pygoban import InputMode, events, get_argparser
from pygoban.events import CursorChanged
from pygoban.move import Empty
from pygoban.player import PassingPlayer, Player
from pygoban.sgf import CR, SQ, TR
from pygoban.startgame import initgame, startgame
from pygoban.status import BLACK, WHITE, get_othercolor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
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

from . import btn_adder, gamewindow
from .filedialog import filename_from_savedialog
from .player import GuiPlayer
from .tree import Tree


class Box(QGroupBox):
    def __init__(self, parent, **kwargs: Any):
        super().__init__(parent)
        self.controller: gamewindow.GameWindow = parent.controller
        self.kwargs = kwargs
        self.init(**kwargs)

    def init(self, **kwargs: Any):
        raise NotImplementedError()


class PlayerBox(Box):
    clock_update_signal = pyqtSignal(int)
    clock_stop_signal = pyqtSignal(int)
    timer = None
    _seconds = 0

    def init(self, player: Player):  # type: ignore
        self.player = player
        self.setTitle(f"{self.player.color}: {self.player.name} ")
        self.setStyleSheet(
            """PlayerBox {{
            margin-top: 4ex; /* leave space at the top for the title */
            border-color: {0};
            border-width : 2px;
            border-style: inset;
            border-radius: 5px;
            padding: 1px 18px 1px 3px;

        }}
        PlayerBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left; /* position at the top center */
            padding: 0 3px;
            border-color: {0};
            border-width : 4px;
            border-style: inset;
            border-radius: 5px;
        }}
        """.format(
                "white" if player.color == WHITE else "black"
            )
        )
        player_layout = QFormLayout()
        self.prisoners_label = QLabel(
            str(self.controller.callbacks["get_prisoners"]()[player.color])
        )
        player_layout.addRow("Prisoners:", self.prisoners_label)
        if self.controller.timesettings:
            hlayout = QHBoxLayout()
            self.clock = QLCDNumber()
            self.byoyomi_label = QLabel("")
            self.clock.display(self.seconds_to_str(0))
            hlayout.addWidget(self.clock)
            hlayout.addWidget(self.byoyomi_label)
            player_layout.addRow(hlayout)
            self.clock_update_signal.connect(self.set_clockdisplay)
            self.clock_stop_signal.connect(self.stop_clockdisplay)
            self.update_byoyomi_label()

        self.setLayout(player_layout)

    def update_controlls(self, _result):
        self.prisoners_label.setText(
            str(self.controller.callbacks["get_prisoners"]()[self.player.color])
        )

    def seconds_to_str(self, seconds):
        hours = int(seconds / 360) if seconds >= 360 else 0
        seconds -= hours * 360
        minutes = int(seconds / 60) if seconds >= 60 else 0
        seconds -= minutes * 60
        txt = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return txt

    def update_byoyomi_label(self):
        if self.controller.timesettings.byoyomi_stones > 1:
            txt = (
                f"  {self.player.clock.byoyomi.stones_left} S"
                if self.player.clock.maintime == 0
                else " - "
            )
        if self.controller.timesettings.byoyomi_num > 1:
            txt = (
                f" {self.player.clock.byoyomi.periods_left} B"
                if self.player.clock.maintime == 0
                else " - "
            )
        self.byoyomi_label.setText(txt)

    def set_clockdisplay(self, seconds):
        self.stop_clockdisplay(seconds)
        self._seconds = seconds
        if seconds > 0:
            self.timer = QTimer(self)
            self.timer.start(1000)
            self.clock.display(self.seconds_to_str(seconds))
            self.timer.timeout.connect(self.clockdisplay_tick)
        else:
            self.clock.display("00:00")
            self.timer = None

    def stop_clockdisplay(self, seconds):
        if self.timer:
            self.timer.stop()
        self.clock.display(self.seconds_to_str(seconds))
        self.update_byoyomi_label()

    def clockdisplay_tick(self):
        self._seconds -= 1
        txt = self.seconds_to_str(self._seconds)
        self.clock.display(txt)


class GameBox(Box):
    def init(self):
        game_layout = QHBoxLayout()
        add_gamebutton = btn_adder(game_layout)
        self.undo_btn = add_gamebutton("Undo", self.do_undo)
        self.pass_btn = add_gamebutton("Pass", self.do_pass)
        self.resign_btn = add_gamebutton("Resign", self.do_resign)
        self.count_btn = add_gamebutton("Count", self.do_count)
        self.setLayout(game_layout)

    def update_controlls(self, _result):
        is_play = (
            self.controller.input_mode == InputMode.PLAY
            and self.controller.gui_mode == gamewindow.GuiMode.PLAY
        )
        self.pass_btn.setEnabled(is_play)
        self.undo_btn.setEnabled(is_play)
        self.resign_btn.setEnabled(is_play)
        self.count_btn.setEnabled(
            self.controller.input_mode == InputMode.COUNT
            or self.controller.gui_mode == gamewindow.GuiMode.EDIT
        )

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
        if isinstance(
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
            "count", is_final=self.controller.input_mode == InputMode.ENDED
        )


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
        if isinstance(result, CursorChanged):
            has_parent = bool(result.cursor and result.cursor.parent)
            self.prev_move.setEnabled(has_parent)
            self.back_moves.setEnabled(has_parent)
            has_children = result.cursor and len(result.cursor.children)
            self.next_move.setEnabled(has_children)
            self.forward_moves.setEnabled(has_children)

    def tree_click(self, move, _col=None):
        self.controller.callbacks["set_cursor"](move)

    def toggle_deco(self, checked):
        self.controller.input_mode = InputMode.DECO if checked else InputMode.PLAY

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
            self.editbox = self.add_box(EditBox(self))

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
        # newwindow_action.triggered.connect(self.assistence)
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

        kwargs = {
            name: self.controller.infos[key]
            for key, name in (
                ("SZ", "boardsize"),
                ("KM", "komi"),
            )
        }
        c = startgame(**kwargs, init_gui=False, root=copy(self.controller.root))[1]
        c.gui_mode = gamewindow.GuiMode.EDIT
        c.sidebar.editbox.do_next_variation()

    def assistence(self):
        assist(cmd="gnugo", orig=self.controller)

    def update_controlls(self, event):
        self.editbox.setVisible(self.controller.gui_mode == gamewindow.GuiMode.EDIT)
        self.gamebox.setVisible(self.controller.gui_mode == gamewindow.GuiMode.PLAY)
        for box in self.boxes:
            if box.isVisible():
                box.update_controlls(event)
        if isinstance(event, events.CursorChanged):
            cmts = event.cursor.extras.comments or [""]
            self.comments.setText("\n".join(cmts))
