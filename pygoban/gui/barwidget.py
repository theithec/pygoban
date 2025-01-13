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

from pygoban import Color, gtp  # , results

from . import GameUI, GUIMode
from .boxes import (
    Box,
    BoxesByName,
    CommentsBox,
)
from .boxes.controlsbox import ControllsBox

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
        self.add_box(CommentsBox(self), vis=is_edit)
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
        # label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(self.btn_settings, 0, Qt.AlignmentFlag.AlignRight)
        self._layout.addRow(settings_layout)
        splitter = QSplitter(self)
        self.inner = BoxesWidget(self)
        splitter.addWidget(self.inner)
        self.tree = Tree(self, callback=self.game_ui.controller.set_cursor)
        self.game_ui.controller.add_receiver(self.tree)
        splitter.addWidget(self.tree)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            """BarWidget {
               padding-right: 20px;
            }
            """
        )
        self.btn_settings.setMenu(self.get_menu())
        # self.turn_done_signal.connect(self.handle_turn_done)
        # self.counted_signal.connect(self.handle_counted)
        # self.clock_update_signal.connect(self.handle_period_done)
        # self.result_done_signal.connect(self.handle_result_done)
        self._layout.addRow(splitter)
        self.setLayout(self._layout)

    def update_menu(self):
        found = False
        for action in self.engines_menu.actions():
            is_connected = action.iconText() not in self.game_ui.controller.connected_engines.keys()
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
        vis = cast(QMenu, menu.addMenu("Show"))
        for name, box in self.inner.boxes.items():
            action = QAction(name, self)
            action.triggered.connect(self.inner.vis_action_handler(box, action))
            action.setCheckable(True)
            box.toggle_action = action
            vis.addAction(action)
            action.setChecked(box.isVisibleTo(self))

        settings_action = QAction("Settings", self)
        menu.addAction(settings_action)

        # settings_action.triggered.connect(self.controller.parent().show_settings_dialog)

        open_action = QAction("Open as new", self)
        open_action.triggered.connect(self.game_ui.open_as_new)
        menu.addAction(open_action)
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_as_file)
        menu.addAction(save_action)
        self.engines_menu = cast(QMenu, menu.addMenu("Engines"))

        def mk_handler(cmd, key):
            def handler():
                gtpctrl, created = self.game_ui.controller.add_controller(
                    gtp.GTPController, cmd_line=cmd, actions=[key]
                )
                if not created:
                    gtpctrl.set_action(key, True)
                self.game_ui.controller.add_receiver(gtpctrl)
                if self.game_ui.last_turn:
                    cpy = copy(self.game_ui.last_turn)
                    cpy.reset = True
                    gtpctrl.receive_game_event(cpy)

            return handler

        engines = self.game_ui.main_ui.settings.gtp_engines
        for name in engines.keys():
            engine_menu = cast(QMenu, self.engines_menu.addMenu(name))

            cmd = engines[name]
            for key in ("analyze", Color.BLACK, Color.WHITE):
                action = QAction(str(key), self)
                action.triggered.connect(mk_handler(cmd, key))
                engine_menu.addAction(action)
            self.engines_menu.addMenu(engine_menu)

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


# class DDD:
#    turn_done_signal = pyqtSignal(results.TurnDone)
#    counted_signal = pyqtSignal(results.Counted)
#    clock_stop_signal = pyqtSignal(int)
#    clock_update_signal = pyqtSignal(results.TimeDone)
#    result_done_signal = pyqtSignal(results.GameResultDone)
#
#    def handle_turn_done(self, result: results.TurnDone):  # type: ignore
#
#        game_box = self.inner.boxes[GameBox.name]
#        assert isinstance(game_box, GameBox)
#        game_box.buttons["Done"].setVisible(False)
#        game_box.buttons["Resign"].setVisible(True)
#
#        players_box = self.inner.players_box
#        player_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
#        for color in (Color.BLACK, Color.WHITE):
#            numdead = result.total_dead[color.other()]
#            player_box = player_boxes[color]
#            player_box.prisoners_label.setText(str(numdead))
#
#        self.tree.setEnabled(self.game_ui.gui_mode == GUIMode.EDIT)
#        self.tree.stones_signal.emit(result.node)
#        if self.game_ui.gui_mode in (GUIMode.EDIT, GUIMode.COUNT):
#            self.inner.edit_box.update_controlls(result)
#
#        if self.game_ui.controller.ruleset.timesettings and result.node.color:
#            game_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
#            box = cast(PlayerGameBox, game_boxes[result.node.color])
#            box.stop_clockdisplay()
#            box.set_clockdisplay(result.node.annos.time_left)
#            box = cast(PlayerGameBox, game_boxes[result.node.color.other()])
#            box.set_clockdisplay(result.node.annos.time_left)
#
#    def handle_result_done(self, result: results.GameResultDone):
#
#        self.tree.setEnabled(True)
#        self.inner.players_box.set_boxes()
#        self.inner.game_box.setVisible(False)
#        self.inner.edit_box.setVisible(True)
#        if self.game_ui.controller.ruleset.timesettings:
#            players_box = self.inner.players_box
#            game_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
#            assert result.winner
#            box = cast(PlayerGameBox, game_boxes[result.winner])
#            num = 0 if result.type == results.GameResultType.LOST_BY_TIME else None
#            box.stop_clockdisplay(seconds=num)
#            box = cast(PlayerGameBox, game_boxes[result.winner.other()])
#            box.stop_clockdisplay(seconds=num)
#
#        assert self.game_ui.last_turn
#        self.inner.edit_box.update_controlls(self.game_ui.last_turn)
#
#    def handle_counted(self, result: results.Counted) -> None:
#        self.tree.setEnabled(False)
#
#        players_box = self.inner.players_box
#
#        # if self.game_ui._initial_gui_mode == GUIMode.PLAY:
#        game_box = self.inner.game_box
#        game_box.buttons["Done"].setVisible(True)
#        #     game_box.buttons["Resign"].setVisible(False)
#
#        next_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
#        players_box.set_boxes()
#        for color in (Color.BLACK, Color.WHITE):
#            box = next_boxes[color]
#            assert isinstance(box, PlayerCountBox), box
#            playerresult = result[color]
#            numcoords = len(playerresult.coords)
#            box.libs_label.setText(str(numcoords))
#            box.prisoners_label.setText(str(playerresult.killed))
#            total = playerresult.total()
#            if box.player.color == Color.WHITE:
#                total += self.game_ui.controller.ruleset.komi
#            box.total_label.setText(str(total))
#
#    def handle_period_done(self, result: results.TimeDone):
#        print("HANDLE", result)
#
#        players_box = self.inner.players_box
#        game_boxes = players_box.boxes_by_mode[self.game_ui.gui_mode]
#        box = cast(PlayerGameBox, game_boxes[result.color])
#        box.set_clockdisplay(result.next_time)
#        # game_boxes[result.color.other()].stop_clockdisplay()
#
