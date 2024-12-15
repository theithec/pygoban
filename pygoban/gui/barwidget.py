# pylint: disable=invalid-name, arguments-differ
# because qt and do_-commands and Box overloading
from typing import TYPE_CHECKING, Any, Callable, Dict, Type, Union

# from PyQt5.QtCore import Qt  # , QTimer, pyqtSignal
from PyQt5.QtCore import Qt, QTimer, pyqtSignal  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QAction,
    QButtonGroup,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLCDNumber,
    QMenu,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
)

from pygoban import Color, Party, results

from . import GUIMode

# from .chart import MyChart
from .tree import Tree


def _(txt):
    return txt


if TYPE_CHECKING:
    from .gamewidget import GameWidget


def btn_adder(
    layout: QLayout, buttoncls: Type[QPushButton] | Type[QRadioButton] = QPushButton
) -> Callable:
    def add_button(label: str, callback: Callable | None = None) -> QPushButton | QRadioButton:
        button = buttoncls(label)
        if callback:
            button.clicked.connect(callback)  # type: ignore
        layout.addWidget(button)
        return button

    return add_button


def seconds_to_str(seconds):
    hours = int(seconds / 360) if seconds >= 360 else 0
    seconds -= hours * 360
    minutes = int(seconds / 60) if seconds >= 60 else 0
    seconds -= minutes * 60
    txt = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return txt


class Box(QGroupBox):
    game_ui: "GameWidget"
    name: str

    def __init__(self, parent: Union["Box", "BarWidget", QFrame], **kwargs):
        super().__init__(parent=parent, visible=kwargs.pop("visible", True))  # type: ignore
        curr: Any = parent
        while str(curr.__class__.__name__) != "GameWidget":
            curr = curr.parent()
        self.game_ui = curr
        self.kwargs = kwargs
        self.init(**kwargs)

    def init(self, **kwargs):
        raise NotImplementedError()


BoxesByName = Dict[str, Box]


class _PlayerBox(Box):
    name = "_Player"
    prisoners_label: QLabel
    byoyomi_label: QLabel
    clock: QLCDNumber

    def __init__(self, parent: "PlayersBox", **kwargs):
        super().__init__(parent, visible=False, **kwargs)

    def init(self, player: Party):  # type: ignore
        self.setTitle(player.name)
        self.player = player

        self.othercolor = Color.WHITE if player.color == Color.BLACK else Color.BLACK
        fg = "#eeeeee" if player.color == Color.BLACK else "#011111"
        bg = "#eeeeee" if player.color == Color.WHITE else "#011111"

        colors = f"""
           background-color : {bg};
           color: {fg} ;
        """
        clsname = self.__class__.__name__
        css1 = f"""
        {clsname} {{
           padding-top: 2ex; /* leave space at the top for the title */
           background-color: {bg};
           {colors}
        }}
        {clsname}::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left; /* position at the top center */
           {colors}
        }}
        QLabel{{
           {colors}
        }}
        QRow#total_row {{
           font-weight: bold;
        }}
        QLabel#total_label{{
           {colors}
           font-weight: bold;
        }}

        """
        self.setStyleSheet(css1)
        self.formlayout = QFormLayout()
        self.prisoners_label = QLabel(str(0))
        self.formlayout.addRow("Prisoners:", self.prisoners_label)


class PlayerGameBox(_PlayerBox):
    timer = None

    def clockdisplay_tick(self):
        self._seconds -= 1
        txt = seconds_to_str(self._seconds)
        self.clock.display(txt)

    def stop_clockdisplay(self, seconds: int | None = None):
        if self.timer:
            self.timer.stop()
        if seconds is not None:
            self.clock.display(seconds_to_str(seconds))

    def set_clockdisplay(self, seconds):
        # seconds = seconds or self._seconds
        self.stop_clockdisplay(seconds)
        self._seconds = seconds

        if seconds > 0:
            self.timer = QTimer(self)
            self.timer.start(1000)
            self.clock.display(seconds_to_str(seconds))
            self.timer.timeout.connect(self.clockdisplay_tick)
        else:
            self.clock.display("00:00")

    def init(self, player: Party, **kwargs) -> None:  # type: ignore
        super().init(player)
        self.clock = QLCDNumber()
        self.byoyomi_label = QLabel("")
        self.clock.display(seconds_to_str(0))
        self.formlayout.addRow(self.clock)
        self.setLayout(self.formlayout)


class PlayerCountBox(_PlayerBox):
    def init(self, player: Party):  # type: ignore
        super().init(player)
        self.libs_label = QLabel(str(0))
        self.formlayout.addRow("Liberties:", self.libs_label)

        if player.color == Color.WHITE:
            self.formlayout.addRow("Komi:", QLabel(str(self.game_ui.controller.ruleset.komi)))
        else:
            self.formlayout.addRow("", QLabel(""))
        self.total_label = QLabel(str(0))
        self.total_label.setObjectName("total_label")
        self.formlayout.addRow("", self.total_label)
        self.setLayout(self.formlayout)


class PlayersBox(Box):
    name = "PlayerBox"
    last_gui_mode: GUIMode = GUIMode.PLAY

    def init(self, players: dict[Color, Party]):  # type: ignore
        self.boxlayout = QHBoxLayout()
        self.boxes_by_mode: dict[GUIMode, dict[Color, PlayerCountBox | PlayerGameBox]] = {
            GUIMode.PLAY: {
                Color.BLACK: PlayerGameBox(self, player=players[Color.BLACK]),
                Color.WHITE: PlayerGameBox(self, player=players[Color.WHITE]),
            },
            GUIMode.COUNT: {
                Color.BLACK: PlayerCountBox(self, player=players[Color.BLACK]),
                Color.WHITE: PlayerCountBox(self, player=players[Color.WHITE]),
            },
        }
        self.boxes_by_mode[GUIMode.EDIT] = self.boxes_by_mode[GUIMode.PLAY]
        for box in self.boxes_by_mode[self.game_ui.gui_mode].values():
            self.last_gui_mode: GUIMode = self.game_ui.gui_mode
            self.boxlayout.addWidget(box)
            box.setVisible(True)
        self.setLayout(self.boxlayout)
        self

    def set_boxes(self):
        print("SET BOXES", self.last_gui_mode, self.game_ui.gui_mode)
        if self.last_gui_mode != self.game_ui.gui_mode:
            curr_boxes = self.boxes_by_mode[self.last_gui_mode]
            next_boxes = self.boxes_by_mode[self.game_ui.gui_mode]
            for color in (Color.BLACK, Color.WHITE):
                self.boxlayout.replaceWidget(
                    curr_boxes[color],
                    next_boxes[color],
                )
                curr_boxes[color].setVisible(False)
                next_boxes[color].setVisible(True)  # True)
        self.last_gui_mode = self.game_ui.gui_mode


class GameBox(Box):
    name = "GameBox"

    def init(self, **kwargs) -> None:
        layout = QHBoxLayout()
        callbacks = self.game_ui.callbacks
        self.action_mapping = {
            "Pass": self.game_ui.controller.do_pass,
            "Resign": lambda: callbacks.set_end_result(
                results.GameResultType.RESIGN, color=self.game_ui.last_turn.next_color
            ),
            "Undo": callbacks.undo,
            "Done": lambda: callbacks.set_end_result(results.GameResultType.COUNTED),
        }

        add_gamebutton = btn_adder(layout)
        self.buttons = {}

        for action in self.action_mapping:
            self.buttons[action] = add_gamebutton(action, self.action_mapping[action])

        self.setLayout(layout)


class EditBox(Box):
    name = "EditBox"

    def init(self):
        box_layout = QFormLayout()
        btns_layout = QHBoxLayout()
        controller = self.game_ui.controller
        add_dirbutton = btn_adder(btns_layout)
        self.btn_first_stone = add_dirbutton("|<", controller.do_first_stone)
        self.btn_prev_var = add_dirbutton("<<", controller.do_prev_variation)
        self.btn_prev_stone = add_dirbutton("<", controller.do_prev_stone)
        self.btn_next_stone = add_dirbutton(">", controller.do_next_stone)
        self.btn_next_var = add_dirbutton(">>", controller.do_next_variation)
        self.btn_last_stone = add_dirbutton(">|", controller.do_last_stone)
        # self.btn_auto = add_dirbutton("auto", controller.toggle_auto)
        self.btn_auto = add_dirbutton("Pass", controller.do_pass)
        self.btn_auto.setCheckable(True)
        # self.btn_count = add_dirbutton("Count", self.toggle_count)
        # self.btn_count.setCheckable(True)

        deco_layout = QHBoxLayout()
        add_decobutton = btn_adder(deco_layout, QRadioButton)
        self.decobox = QGroupBox("Deco")
        self.decogroup = QButtonGroup()
        self.decobox.setCheckable(True)
        self.decobox.setChecked(False)
        self.decobox.toggled.connect(self.toggle_deco)
        self.decogroup.addButton(add_decobutton("B"))
        self.decogroup.addButton(add_decobutton("W"))
        self.decogroup.addButton(add_decobutton("TR"))
        self.decogroup.addButton(add_decobutton("SQ"))
        self.decogroup.addButton(add_decobutton("CR"))
        self.decogroup.addButton(add_decobutton("1"))
        self.decogroup.addButton(add_decobutton("A"))
        self.decobox.setLayout(deco_layout)

        box_layout.addRow(btns_layout)
        box_layout.addRow(self.decobox)
        self.setLayout(box_layout)

    def toggle_deco(self):
        self.game_ui.is_annotating = self.decobox.isChecked()

    def do_nr(self):
        pass

    def do_char(self):
        pass

    def update_controlls(self, result):
        stone = result.stone
        has_parent = bool(stone.parent)
        has_children = bool(stone.children)
        self.btn_first_stone.setEnabled(has_parent)
        self.btn_prev_var.setEnabled(has_parent)
        self.btn_prev_stone.setEnabled(has_parent)
        self.btn_next_stone.setEnabled(has_children)
        self.btn_next_var.setEnabled(has_children)
        self.btn_last_stone.setEnabled(has_children)


class CommentsBox(Box):
    name = "CommentsBox"

    def init(self):  # type: ignore
        layout = QHBoxLayout()
        self.comments = QTextEdit()
        layout.addWidget(self.comments)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setLayout(layout)

    def update_controlls(self, result):
        if stone_result := result.stone_result:
            self.comments.setText(stone_result.stone.annos.comment)


class ChartBox(Box):
    name = "ChartBox"

    def init(self):  # type: ignore
        layout = QHBoxLayout()
        self.chart = MyChart()
        layout.addWidget(self.chart)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setLayout(layout)

    def update_controlls(self, result):
        assert self.controller.curr_action_result
        self.chart.add_data()


class InnerWidget(QFrame):
    def __init__(self, parent: "BarWidget"):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.game_ui = parent.game_ui
        self.boxes: BoxesByName = {}
        is_edit = self.game_ui.gui_mode == GUIMode.EDIT
        pbox = PlayersBox(self, players=self.game_ui.parties)
        self.playersbox: PlayersBox = self.add_box(pbox, vis=True)
        self.add_box(GameBox(self), vis=not is_edit)
        self.add_box(EditBox(self), vis=is_edit)
        self.add_box(CommentsBox(self), vis=is_edit)
        # self.add_box(ChartBox(self), vis=True)
        self._layout.addRow("Ruleset", QLabel("Some data"))
        self.setLayout(self._layout)

    def add_box(self, box: Box, vis: bool) -> Box:
        self.boxes[box.name] = box
        self._layout.addRow(box)
        box.setVisible(vis)
        return box

    def vis_action_handler(self, box: Box, action):
        def handle():
            checked = action.isChecked()
            box.setVisible(checked)
            if checked:
                assert self.game_ui.curr_action_result
                self.update_controlls(result=self.game_ui.curr_action_result)

        return handle


class BarWidget(QFrame):
    turn_done_signal = pyqtSignal(results.TurnDone)
    counted_signal = pyqtSignal(results.Counted)
    clock_stop_signal = pyqtSignal(int)
    clock_update_signal = pyqtSignal(results.TimeDone)
    result_done_signal = pyqtSignal(results.GameResultDone)

    game_ui: "GameWidget"

    def __init__(self, parent: "GameWidget"):
        self.game_ui = parent
        super().__init__(parent)
        self._layout = QFormLayout()
        self.btn_settings = QPushButton("\u2630")
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.btn_settings, 0, Qt.AlignRight)
        self._layout.addRow(settings_layout)
        splitter = QSplitter(self)
        self.inner = InnerWidget(self)
        splitter.addWidget(self.inner)
        self.tree = Tree(self, callback=self.game_ui.controller.callbacks.set_cursor)
        splitter.addWidget(self.tree)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            """BarWidget {
               padding-right: 20px;
            }
            """
        )
        self.btn_settings.setMenu(self.get_menu())
        self.turn_done_signal.connect(self.handle_turn_done)
        self.counted_signal.connect(self.handle_counted)
        self.clock_update_signal.connect(self.handle_period_done)
        self.result_done_signal.connect(self.handle_result_done)
        self._layout.addRow(splitter)
        self.setLayout(self._layout)

    def update_menu(self):
        return
        found = False
        for action in self.engines_menu.actions():
            is_connected = action.iconText() not in self.game_ui.controller.connected_engines.keys()
            action.setEnabled(is_connected)
            found = found or is_connected
        if found:
            pass

    def get_menu(self) -> QMenu:
        menu = QMenu(self)
        # new_ = menu.addMenu("New")
        # for name, callback in (
        #    (_("New Game"), self.parent().show_add_game_dialog),
        #    (_("Edit Board"), self.controller.parent().show_edit_board_dialog),
        # ):
        #    action = QAction(name, self)
        #    new_.addAction(action)  # type: ignore
        #    action.triggered.connect(callback)
        vis = menu.addMenu("Show")
        for name, box in self.inner.boxes.items():
            action = QAction(name, self)
            action.triggered.connect(self.inner.vis_action_handler(box, action))
            action.setCheckable(True)
            box.toggle_action = action
            vis.addAction(action)  # type: ignore

        settings_action = QAction("Settings", self)
        menu.addAction(settings_action)

        # settings_action.triggered.connect(self.controller.parent().show_settings_dialog)

        open_action = QAction("Open as new", self)
        open_action.triggered.connect(self.game_ui.open_as_new)
        menu.addAction(open_action)
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_as_file)
        menu.addAction(save_action)
        self.engines_menu = menu.addMenu("Engines")

        def mk_handler(name, cmd, key):
            def handler():
                self.game_ui.connect_engine(name, cmd, key)

            return handler

        # for name in self.controller.controller.settings["gtp_engines"].keys():
        #    engine_menu = self.engines_menu.addMenu(name)

        #    cmd = self.controller.controller.settings["gtp_engines"][name]
        #    for key in ("analyze", Color.BLACK.name, Color.WHITE.name):
        #        action = QAction(key, self)
        #        action.triggered.connect(mk_handler(name, cmd, key))
        #        engine_menu.addAction(action)
        #    self.engines_menu.addMenu(engine_menu)

        return menu

    def handle_turn_done(self, result: results.TurnDone):  # type: ignore

        game_box = self.inner.boxes[GameBox.name]
        assert isinstance(game_box, GameBox)
        game_box.buttons["Done"].setVisible(False)
        game_box.buttons["Resign"].setVisible(True)

        players_box = self.inner.playersbox
        assert isinstance(players_box, PlayersBox)
        player_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
        for color in (Color.BLACK, Color.WHITE):
            numdead = result.total_dead[color.other()]
            player_box = player_boxes[color]
            player_box.prisoners_label.setText(str(numdead))

        self.tree.setEnabled(self.game_ui.gui_mode == GUIMode.EDIT)
        self.tree.stones_signal.emit(result.stone)
        print("GUIMODE", self.game_ui.gui_mode)
        if self.game_ui.gui_mode in (GUIMode.EDIT, GUIMode.COUNT):
            self.inner.boxes[EditBox.name].update_controlls(result)

        if self.game_ui.ruleset.timesettings and result.stone.color:

            players_box = self.inner.playersbox
            assert isinstance(players_box, PlayersBox)
            game_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
            game_boxes[result.stone.color].stop_clockdisplay()
            game_boxes[result.stone.color.other()].set_clockdisplay(result.stone.annos.time_left)

    def handle_result_done(self, result: results.GameResultDone):

        self.tree.setEnabled(True)
        self.inner.playersbox.set_boxes()
        self.inner.boxes[GameBox.name].setVisible(False)
        self.inner.boxes[EditBox.name].setVisible(True)
        if self.game_ui.ruleset.timesettings:
            players_box = self.inner.playersbox
            assert isinstance(players_box, PlayersBox)
            game_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
            game_boxes[result.winner].stop_clockdisplay()
            num = 0 if result.type == results.GameResultType.LOST_BY_TIME else None
            print("RE", result, result.type, num)
            game_boxes[result.winner.other()].stop_clockdisplay(seconds=num)
            game_boxes[result.winner].stop_clockdisplay()

        self.inner.boxes[EditBox.name].update_controlls(self.game_ui.last_turn)

    def handle_counted(self, result: results.Counted) -> None:
        self.tree.setEnabled(False)

        players_box = self.inner.playersbox
        assert isinstance(players_box, PlayersBox)

        if self.game_ui._initial_gui_mode == GUIMode.PLAY:
            game_box = self.inner.boxes[GameBox.name]
            assert isinstance(game_box, GameBox)
            game_box.buttons["Done"].setVisible(True)
            game_box.buttons["Resign"].setVisible(False)

        next_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
        players_box.set_boxes()
        for color in (Color.BLACK, Color.WHITE):
            box = next_boxes[color]
            assert isinstance(box, PlayerCountBox), box
            playerresult = result[color]
            numcoords = len(playerresult.coords)
            box.libs_label.setText(str(numcoords))
            box.prisoners_label.setText(str(playerresult.killed))
            total = playerresult.total()
            if box.player.color == Color.WHITE:
                total += self.game_ui.controller.ruleset.komi
            box.total_label.setText(str(total))

    def handle_period_done(self, result: results.TimeDone):
        print("HANDLE", result)

        players_box = self.inner.playersbox
        assert isinstance(players_box, PlayersBox)
        game_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
        game_boxes[result.color].set_clockdisplay(result.next_time)
        # game_boxes[result.color.other()].stop_clockdisplay()

    def save_as_file(self):
        pass

    # def save_as_file(self):
    #    name = filename_from_savedialog(self)
    #    with open(name, "w") as fileobj:
    #        fileobj.write(self.gamewidget.to_sgf())
    #    with open(name, "w") as fileobj:
    #        fileobj.write(self.gamewidget.to_sgf())
    #        fileobj.write(self.gamewidget.to_sgf())
