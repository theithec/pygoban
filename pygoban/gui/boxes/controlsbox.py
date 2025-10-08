# pylint: disable=abstract-method
from typing import cast

from PyQt6.QtGui import QIcon  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module; QFormLayout,
    QButtonGroup,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
)

from pygoban import results
from pygoban.gui import BASE_DIR, GUIMode

from . import Box, btn_adder


class GameBox(Box):
    name = "GameBox"

    def init(self, **kwargs) -> None:
        layout = QHBoxLayout()
        controller = self.game_ui.controller
        self.action_mapping = {
            "Pass": self.game_ui.controller.do_pass,
            "Resign": lambda: controller.set_end_result(
                results.GameResultType.RESIGN,
                color=cast(results.TurnDone, self.game_ui.last_turn).next_color,
            ),
            "Undo": self.game_ui.undo,
            "Done": lambda: controller.set_end_result(results.GameResultType.COUNTED),
        }

        add_gamebutton = btn_adder(layout)
        self.buttons = {}

        for action, mapping in self.action_mapping.items():
            self.buttons[action] = add_gamebutton(action, mapping)
        self.buttons["Done"].setVisible(False)
        self.setLayout(layout)


class EditBox(Box):
    name = "EditBox"

    def init(self, **_kwargs):
        box_layout = QVBoxLayout()
        btns_layout1 = QHBoxLayout()
        controller = self.game_ui.controller
        add_dirbutton = btn_adder(btns_layout1)
        self.btn_first_stone = add_dirbutton("|<", controller.do_first_stone)
        self.btn_prev_var = add_dirbutton("<<", controller.do_prev_variation)
        self.btn_prev_stone = add_dirbutton("<", controller.do_prev_stone)
        self.btn_next_stone = add_dirbutton(">", controller.do_next_stone)
        self.btn_next_var = add_dirbutton(">>", controller.do_next_variation)
        self.btn_last_stone = add_dirbutton(">|", controller.do_last_stone)
        # self.btn_auto = add_dirbutton("auto", controller.toggle_auto)
        btns_layout2 = QHBoxLayout()
        add_dirbutton = btn_adder(btns_layout2)
        self.btn_auto = add_dirbutton("Pass", controller.do_pass)
        # self.btn_auto.setCheckable(True)
        self.btn_count = add_dirbutton("Count", self.toggle_count)
        self.btn_count.setCheckable(True)

        deco_layout = QGridLayout()

        def mk_decobutton_callback(text: str):
            def callback(*args, **kwargs):
                self.game_ui.annotation_type = text

            return callback

        def add_decobutton(
            x, y, key: str, label: str | None = None, icon: str | None = None
        ) -> QRadioButton:
            label = label or key
            btn = QRadioButton(parent=self, text=label)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            btn.clicked.connect(mk_decobutton_callback(key))  # type: ignore
            if icon:
                btn.setIcon(QIcon(icon))
            deco_layout.addWidget(btn, x, y)
            return btn

        self.decobox = QGroupBox("Deco")
        self.decogroup = QButtonGroup()
        self.decobox.setCheckable(True)
        self.decobox.setChecked(False)
        self.decobox.toggled.connect(self.toggle_deco)
        self.decogroup.addButton(
            add_decobutton(0, 0, "B", icon=f"{BASE_DIR}/gui/imgs/black.png")
        )
        self.decogroup.addButton(
            add_decobutton(0, 1, "W", icon=f"{BASE_DIR}/gui/imgs/white.png")
        )
        self.decogroup.addButton(add_decobutton(1, 0, "TR", "△"))
        self.decogroup.addButton(add_decobutton(1, 1, "SQ", "□"))
        self.decogroup.addButton(add_decobutton(1, 2, "CR", "○"))
        self.decogroup.addButton(add_decobutton(2, 0, "1", "1 ..."))
        self.decogroup.addButton(add_decobutton(2, 1, "A", "A ..."))
        self.decogroup.addButton(add_decobutton(3, 0, "LN", "－"))
        self.decogroup.addButton(add_decobutton(3, 1, "AR", "→"))
        self.decobox.setLayout(deco_layout)

        # box_layout.addLayout(btns_layout1)
        box_layout.addLayout(btns_layout1)
        box_layout.addLayout(btns_layout2)
        box_layout.addWidget(self.decobox)
        self.setLayout(box_layout)

    def toggle_count(self):
        if self.game_ui.gui_mode == GUIMode.EDIT:
            self.game_ui.gui_mode = GUIMode.COUNT
            self.game_ui.controller.count()
        elif self.game_ui.gui_mode == GUIMode.COUNT:
            self.game_ui.gui_mode = GUIMode.EDIT
        self.game_ui.boardwidget.update()

    def toggle_deco(self):
        if not self.decobox.isChecked():
            self.game_ui.annotation_type = ""

    def do_nr(self):
        pass

    def do_char(self):
        pass

    def update_controlls(self, result: results.TurnDone):
        has_parent = bool(result.node.parent)
        has_children = bool(result.node.children)
        self.btn_first_stone.setEnabled(has_parent)
        self.btn_prev_var.setEnabled(has_parent)
        self.btn_prev_stone.setEnabled(has_parent)
        self.btn_next_stone.setEnabled(has_children)
        self.btn_next_var.setEnabled(has_children)
        self.btn_last_stone.setEnabled(has_children)

    def mode_changed(self, gui_mode):
        self.btn_count.setChecked(gui_mode == GUIMode.COUNT)


class ControllsBox(Box):
    name = "ctrls"

    def init(self, **_kwargs):
        layout = QHBoxLayout()
        gui_mode = self.game_ui.gui_mode
        self.game_box = GameBox(self, visible=gui_mode == GUIMode.PLAY)
        layout.addWidget(self.game_box)
        self.edit_box = EditBox(self, visible=gui_mode == GUIMode.EDIT)
        layout.addWidget(self.edit_box)
        self.setLayout(layout)
        self.events = {results.TurnDone}

    def received_turn(self, result: results.TurnDone):
        self.game_box.buttons["Done"].setVisible(False)
        self.game_box.buttons["Pass"].setVisible(True)
        self.game_box.buttons["Undo"].setEnabled(not result.node.is_root)
        if self.game_ui.gui_mode == GUIMode.EDIT:
            self.edit_box.update_controlls(result)

    def mode_changed(self, gui_mode):
        match gui_mode:
            case GUIMode.COUNT:
                self.game_box.buttons["Done"].setVisible(True)
                self.game_box.buttons["Pass"].setVisible(False)
            case GUIMode.PLAY:
                self.game_box.setVisible(True)
                self.edit_box.setVisible(False)
                self.game_box.buttons["Done"].setVisible(False)
                self.game_box.buttons["Pass"].setVisible(True)
            case GUIMode.EDIT:
                self.game_box.setVisible(False)
                self.edit_box.setVisible(True)
