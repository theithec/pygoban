# pylint: disable=invalid-name, arguments-differ
# because qt and do_-commands and Box overloading
from copy import copy
from typing import TypeVar, cast

from PyQt6.QtCore import Qt  # , pyqtSignal  # pylint: disable=no-name-in-module
from PyQt6.QtGui import QAction  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QWidget,
)

from pygoban import Color, gtp
from pygoban.sgf import writer

from . import GameUI, GUIMode, filedialog
from .boxes import Box, BoxesByName, CommentsBox
from .boxes.controlsbox import ControllsBox
from .boxes.diagram2 import DiagramBox
from .boxes.playersbox import PlayersBox

# from .chart import MyChart
from .tree import Tree


def _(txt):
    return txt


B = TypeVar("B", bound=Box)


class BoxesWidget(QWidget):
    def __init__(self, parent: "BarWidget"):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.game_ui = parent.game_ui
        self.boxes: BoxesByName = {}
        is_edit = self.game_ui.gui_mode == GUIMode.EDIT
        pbox = PlayersBox(self, players=self.game_ui.parties)
        self.players_box = self.add_box(pbox, vis=True)
        # self.game_box = self.add_box(GameBox(self), vis=not is_edit)
        # self.edit_box = self.add_box(EditBox(self), vis=is_edit)
        self.ctrl_box = self.add_box(ControllsBox(self), vis=True)
        # self.add_box(CommentsBox(self), vis=is_edit)
        self.add_box(CommentsBox(self), vis=False)
        self.add_box(DiagramBox(self), vis=is_edit)
        self._layout.addRow("Ruleset", QLabel("Some data"))
        self.setLayout(self._layout)

    def add_box(self, box: B, vis: bool) -> B:
        self.boxes[box.name] = box
        self._layout.addRow(box)
        box.setVisible(vis)
        return box

    def vis_action_handler(self, box: Box, action):
        def handle():
            checked = action.isChecked()
            box.setVisible(checked)
            # if checked:
            #    assert self.game_ui.last_turn
            #    box.update_controlls(result=self.game_ui.last_turn)

        return handle


class BarWidget(QFrame):
    game_ui: GameUI

    def __init__(self, parent: GameUI):
        self.game_ui = parent
        super().__init__(parent)
        self._layout = QFormLayout()
        self.btn_settings = QPushButton("\u2630")
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.btn_settings, 0, Qt.AlignmentFlag.AlignRight)
        self._layout.addRow(settings_layout)
        splitter = QSplitter(self)
        self.inner = BoxesWidget(self)
        splitter.addWidget(self.inner)
        self.tree = Tree(self, callback=self.game_ui.controller.set_cursor)
        self.game_ui.controller.add_receiver(self.tree)
        splitter.addWidget(self.tree)
        splitter.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.btn_settings.setMenu(self.get_menu())
        self._layout.addRow(splitter)
        self.setLayout(self._layout)

    def update_menu(self):
        found = False
        for action in self.engines_menu.actions():
            is_connected = (
                action.iconText()
                not in self.game_ui.controller.connected_engines.keys()
            )
            action.setEnabled(is_connected)
            found = found or is_connected
        if found:
            pass

    def get_menu(self) -> QMenu:
        menu = QMenu(self)
        new_ = menu.addMenu("New")
        for name, callback in (
            (_("New Game"), self.game_ui.main_ui.show_add_game_dialog),
            (_("Edit Board"), self.game_ui.main_ui.show_edit_board_dialog),
        ):
            action = QAction(name, self)
            new_.addAction(action)  # type: ignore
            action.triggered.connect(callback)
        vis = cast(QMenu, menu.addMenu("View"))
        for name, box in self.inner.boxes.items():
            action = QAction(name, self)
            action.triggered.connect(self.inner.vis_action_handler(box, action))
            action.setCheckable(True)
            box.toggle_action = action
            vis.addAction(action)
            action.setChecked(box.isVisibleTo(self))

        settings_action = QAction("Settings", self)
        menu.addAction(settings_action)

        settings_action.triggered.connect(self.game_ui.parent().show_settings_dialog)

        open_action = QAction("Open as new", self)
        open_action.triggered.connect(self.game_ui.open_as_new)
        menu.addAction(open_action)
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_as_file)
        menu.addAction(save_action)
        open_action = QAction("Open file", self)
        open_action.triggered.connect(self.open_file)
        menu.addAction(open_action)
        self.engines_menu = cast(QMenu, menu.addMenu("Engines"))

        def mk_handler(name, cmd, key):
            def handler():
                print("hanlde", cmd, key)

                gtpctrl, created = self.game_ui.controller.add_controller(
                    gtp.GTPController,
                    name=name,
                    cmd_line=cmd,
                    actions=[key],  # , key=name
                )
                if not created:
                    gtpctrl.set_action(key, True)
                self.game_ui.controller.add_receiver(gtpctrl)
                if self.game_ui.last_turn:
                    if key == "analyze_full":
                        # self.game_ui.controller.set_cursor(self.game_ui.last_turn.node.root())
                        pass
                    cpy = copy(self.game_ui.last_turn)
                    cpy.reset = True
                    gtpctrl.receive_game_event(cpy)

            return handler

        engines = self.game_ui.main_ui.settings.gtp_engines
        for name in engines.keys():
            engine_menu = cast(QMenu, self.engines_menu.addMenu(name))

            cmd = engines[name]
            for key in ("analyze", "analyze_full", Color.BLACK, Color.WHITE):
                action = QAction(str(key), self)
                action.triggered.connect(mk_handler(name, cmd, key))
                engine_menu.addAction(action)
            self.engines_menu.addMenu(engine_menu)

        return menu

    def save_as_file(self):
        path = filedialog.filename_from_savedialog(parent=self)
        if not path:
            return
        txt = writer.write(self.game_ui.last_turn.node, self.game_ui.controller.ruleset)
        with open(path, "w", encoding="utf-8") as fobj:
            fobj.write(txt)

    def open_file(self) -> None:
        path = filedialog.filename_from_opendialog(parent=self)
        self.game_ui.main_ui.load_sgf(path)
