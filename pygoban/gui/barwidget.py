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

from pygoban import ActionResult, ActionType, Color, GameController, GameResult, Party

from . import GUIMode

# from .chart import MyChart
# from .tree import Tree

# from pygoban.stone import Annotations


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
    controller: "GameWidget"
    name: str

    def __init__(self, parent: Union["Box", "BarWidget", QFrame], **kwargs):
        super().__init__(parent=parent, visible=kwargs.pop("visible", True))  # type: ignore
        curr: Any = parent
        while (
            str(curr.__class__.__name__) != "GameWidget"
        ):  # not issubclass(type(curr), GameController):
            curr = curr.parent()
        # self.controller = curr
        self.game_ui = curr
        self.kwargs = kwargs
        self.init(**kwargs)

    def init(self, **kwargs: Any):
        raise NotImplementedError()

    def update_controlls(self, result: ActionResult):
        raise NotImplementedError(self)


BoxesByName = Dict[str, Box]


class _PlayerBox(Box):
    name = "Players"
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
        {
        clsname}::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left; /* position at the top center */
           {colors}
        }}
        QLabel{{
           {colors}
        }}

        """
        self.setStyleSheet(css1)
        self.formlayout = QFormLayout()
        self.prisoners_label = QLabel(str(0))
        self.formlayout.addRow("Prisoners:", self.prisoners_label)

    def update_controlls(self, result: ActionResult):
        pass


class PlayerGameBox(_PlayerBox):
    clock_update_signal = pyqtSignal(int)
    clock_stop_signal = pyqtSignal(int)

    timer = None

    def clockdisplay_tick(self):
        self._seconds -= 1
        txt = seconds_to_str(self._seconds)
        self.clock.display(txt)

    def stop_clockdisplay(self, seconds):
        if self.timer:
            self.timer.stop()
        self.clock.display(seconds_to_str(seconds))
        # self.update_byoyomi_label()

    def set_clockdisplay(self, seconds):
        self.stop_clockdisplay(seconds)
        self._seconds = seconds

        if seconds > 0:
            self.timer = QTimer(self)
            self.timer.start(1000)
            self.clock.display(seconds_to_str(seconds))
            self.timer.timeout.connect(self.clockdisplay_tick)
        else:
            self.clock.display("00:00")

    def init(self, player: Party, **kwargs):  # type: ignore
        super().init(player)
        self.clock = QLCDNumber()
        self.byoyomi_label = QLabel("")
        self.clock.display(seconds_to_str(0))
        self.formlayout.addRow(self.clock)
        self.setLayout(self.formlayout)
        self.clock_update_signal.connect(self.set_clockdisplay)
        self.clock_stop_signal.connect(self.stop_clockdisplay)

    def update_controlls(self, result: ActionResult):  # type: ignore
        if result.stone_result:
            numdead = result.total_dead[self.othercolor]
            self.prisoners_label.setText(str(numdead))


class PlayerCountBox(_PlayerBox):
    def init(self, player: Party):  # type: ignore
        super().init(player)
        self.libs_label = QLabel(str(0))
        self.formlayout.addRow("Liberties:", self.libs_label)

        if player.color == Color.WHITE:
            self.formlayout.addRow("Komi:", QLabel(str(self.game_ui.controller.ruleset.komi)))
        self.total_label = QLabel(str(0))
        self.formlayout.addRow("Total:", self.total_label)
        self.setLayout(self.formlayout)

    # def update_controlls(self, result: GameResult):  # type: ignore
    #    playerresult = result[self.player.color]
    #    if playerresult:
    #        numcoords = len(playerresult.coords)
    #        self.libs_label.setText(str(numcoords))
    #        assert self.controller.curr_action_result
    #        numdead = self.controller.curr_action_result.dead[self.othercolor] + playerresult.killed
    #        self.prisoners_label.setText(str(numdead))
    #        total = numdead + numcoords
    #        if self.player.color == Color.WHITE:
    #            total += self.controller.ruleset.komi
    #        self.total_label.setText(str(total))


class PlayersBox(Box):
    name = "Players"
    last_gui_mode: GUIMode = GUIMode.PLAY

    def init(self, players: Dict[Color, Party]):  # type: ignore
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
            # Color.WHITE: PlayerBox(self, player=players[Color.WHITE]),
        }
        # for box in self.boxes_by_mode[self.controller.gui_mode].values():
        self.boxes_by_mode[GUIMode.EDIT] = self.boxes_by_mode[GUIMode.PLAY]
        for box in self.boxes_by_mode[self.game_ui.gui_mode].values():
            self.last_gui_mode: GUIMode = self.game_ui.gui_mode
            self.boxlayout.addWidget(box)
            box.setVisible(True)
        self.setLayout(self.boxlayout)

    def update_controlls(self, result: ActionResult):
        curr_boxes = self.boxes_by_mode[self.last_gui_mode]
        next_boxes = self.boxes_by_mode[self.game_ui.gui_mode]
        if self.last_gui_mode != self.game_ui.gui_mode:
            for color in (Color.BLACK, Color.WHITE):
                self.boxlayout.replaceWidget(
                    curr_boxes[color],
                    next_boxes[color],
                )
                curr_boxes[color].setVisible(False)
                next_boxes[color].setVisible(True)
        self.last_gui_mode = self.game_ui.gui_mode

        for box in next_boxes.values():
            # if isinstance(result, GameResult):
            box.update_controlls(result)

        # #].items():
        # for color, box in self.boxes[self.controller.gui_mode].items():
        # for color, box in self.boxes[self.controller.gui_mode].items():
        # othercolor = Color.WHITE if color == Color.BLACK else Color.BLACK
        # if isinstance(result, ActionResult):
        #    box.prisoners_label.setText(str(result.dead[othercolor]))
        #    box.libs_label.setVisible(False)
        #    box.total_label.setVisible(False)
        # elif isinstance(result, GameResult):
        #    box.libs_label.setVisible(True)
        #    box.total_label.setVisible(True)
        #    numcoords = len(result[color].coords)
        #    box.libs_label.setText(str(numcoords))
        #    numdead = self.controller.curr_action_result.dead[othercolor] + result[color].killed
        #    box.prisoners_label.setText(str(numdead))
        #    box.total_label.setText(str(numdead + numcoords))


class GameBox(Box):
    name = "Play-Mode"

    def init(self):  # type: ignore
        layout = QHBoxLayout()
        callbacks = self.game_ui.callbacks
        self.action_mapping = {
            "Pass": self.game_ui.controller.do_pass,
            ActionType.RESIGN.value: callbacks.resign,
            "Undo": callbacks.undo,
            # "Done": self.game_ui.controller.count_done,
            # GameResultType.END: callbacks.end_result,
        }

        add_gamebutton = btn_adder(layout)
        self.buttons = {}

        for action in self.action_mapping:
            self.buttons[action] = add_gamebutton(action, self.action_mapping[action])

        self.setLayout(layout)

    def update_controlls(self, result: ActionResult):
        pass
        # is_game_result = type(result) == GameResult
        # self.buttons[GameResultType.END].setVisible(is_game_result)
        # self.buttons["Pass"].setVisible(not is_game_result)
        # self.buttons["Done"].setVisible(result.type == ActionType.COUNT)


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
        self.controller.is_annotating = self.decobox.isChecked()

    def do_nr(self):
        pass

    def do_char(self):
        pass

    # def toggle_count(self):
    #     if self.btn_count.isChecked():
    #         self.ctrl.gui_mode = GUIMode.COUNT
    #     else:
    #         self.ctrl.gui_mode = GUIMode.EDIT
    #     # self.ctrl.boardwidget.update_intersections(
    #     #    self.ctrl.ruleset.count(self.ctrl.curr_action_result.board)
    #     # )

    def update_controlls(self, result: ActionResult):
        if type(result) == ActionResult:
            stone = result.stone
            has_parent = bool(stone.parent)
            has_children = bool(stone.children)
            self.btn_first_stone.setEnabled(has_parent)
            self.btn_prev_var.setEnabled(has_parent)
            self.btn_prev_stone.setEnabled(has_parent)
            self.btn_next_stone.setEnabled(has_children)
            self.btn_next_var.setEnabled(has_children)
            self.btn_last_stone.setEnabled(has_children)
            # self.forward_stones.setEnabled(has_children)


class CommentsBox(Box):
    name = "Comments"

    def init(self):  # type: ignore
        layout = QHBoxLayout()
        self.comments = QTextEdit()
        layout.addWidget(self.comments)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setLayout(layout)

    def update_controlls(self, result: ActionResult):
        assert self.controller.curr_action_result
        self.comments.setText(self.controller.curr_action_result.stone.annos.comment)


class ChartBox(Box):
    name = "Chart"

    def init(self):  # type: ignore
        layout = QHBoxLayout()
        self.chart = MyChart()
        layout.addWidget(self.chart)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setLayout(layout)

    def update_controlls(self, result: ActionResult):
        assert self.controller.curr_action_result
        self.chart.add_data()
        # self.comments.setText(self.controller.curr_action_result.stone.annos.comment)


class InnerWidget(QFrame):
    def __init__(self, parent: "BarWidget"):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.controller = parent.controller
        self.boxes: BoxesByName = {}
        is_edit = self.controller.gui_mode == GUIMode.EDIT
        pbox = PlayersBox(self, players=self.controller.parties)
        self.playersbox = self.add_box(pbox, vis=True)
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
                assert self.controller.curr_action_result
                self.update_controlls(result=self.controller.curr_action_result)

        return handle

    def update_controlls(self, result: ActionResult):
        for box in self.boxes.values():
            if box.isVisible():
                print("UPDATE BOX", box)
                box.update_controlls(result)


class BarWidget(QFrame):
    result_signal = pyqtSignal(ActionResult)
    controller: "GameWidget"

    def __init__(self, parent: "GameWidget"):
        self.controller = parent
        super().__init__(parent)
        self._layout = QFormLayout()
        self.btn_settings = QPushButton("\u2630")
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.btn_settings, 0, Qt.AlignRight)
        self._layout.addRow(settings_layout)
        splitter = QSplitter(self)
        self.inner = InnerWidget(self)
        splitter.addWidget(self.inner)
        # elf.tree = Tree(self, callback=self.controller.game_callbacks.set_cursor)
        # splitter.addWidget(self.tree)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            """BarWidget {
               padding-right: 20px;
            }
            """
        )
        self.btn_settings.setMenu(self.get_menu())
        self.result_signal.connect(self.update_controlls)
        self._layout.addRow(splitter)
        self.setLayout(self._layout)

    def update_menu(self):
        return
        found = False
        for action in self.engines_menu.actions():
            is_connected = action.iconText() not in self.controller.connected_engines.keys()
            action.setEnabled(is_connected)
            found = found or is_connected
        if found:
            pass

    def update_controlls(self, result: ActionResult):
        # self.tree.setEnabled(self.controller.gui_mode == GUIMode.EDIT)
        # if result.stone_result:
        #     self.tree.stones_signal.emit(result.stone_result.stone)
        self.inner.update_controlls(result)
        # for box in self.inner.boxes.values():
        #    box.toggle_action.setChecked(box.isVisible())
        self.update_menu()

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
        open_action.triggered.connect(self.controller.open_as_new)
        menu.addAction(open_action)
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_as_file)
        menu.addAction(save_action)
        self.engines_menu = menu.addMenu("Engines")

        def mk_handler(name, cmd, key):
            def handler():
                self.controller.connect_engine(name, cmd, key)

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

    def save_as_file(self):
        pass

    # def save_as_file(self):
    #    name = filename_from_savedialog(self)
    #    with open(name, "w") as fileobj:
    #        fileobj.write(self.gamewidget.to_sgf())
    #    with open(name, "w") as fileobj:
    #        fileobj.write(self.gamewidget.to_sgf())
    #        fileobj.write(self.gamewidget.to_sgf())
