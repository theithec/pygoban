# pylint: disable=invalid-name
# because qt
import os
from copy import copy

from PyQt6.QtCore import pyqtSignal, QUrl  # pylint: disable=no-name-in-module

# from PyQt6.QtMultimedia import QSound  # pylint: disable=no-name-in-module
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtGui import QCloseEvent  # pylint: disable=no-name-in-module
from .. import (
    BaseReceiver,
    Color,
    GameController,
    Marker,
    Parties,
    results,
)
from . import BASE_DIR, GameUI, GUIMode, MainUI
from .barwidget import BarWidget
from .boardwidget import BoardWidget, BoardOverlay
from .intersections import IntersectionWidget
from .players import GUIPlayer


class GuiReceiver(BaseReceiver):
    def __init__(self, game_ui: "GameWidget"):
        super().__init__()
        self.events = {
            results.TurnDone,
            results.AnnotationDone,
            results.ColorResult,
            results.Counted,
            results.GameResultDone,
        }
        self.game_ui: "GameWidget" = game_ui

    def received_turn(self, result: results.TurnDone) -> None:
        self.game_ui.last_turn = result
        self.game_ui.boardwidget.update()

    def received_resign(self, result) -> None:
        pass

    def received_annotated(self, result) -> None:
        self.game_ui.boardwidget.update()

    def received_count(self, result) -> None:
        self.game_ui.gui_mode = GUIMode.COUNT
        assert self.game_ui.last_turn
        for color in (Color.BLACK, Color.WHITE):
            result[color].killed += self.game_ui.last_turn.total_dead[color.other()]
        self.game_ui.boardwidget.update()

    def received_result_done(self, result: results.GameResultDone) -> None:
        self.game_ui.gui_mode = GUIMode.EDIT
        self.game_ui.boardwidget.update()


class GameWidget(GameUI):
    gameended_signal = pyqtSignal(str)

    def __init__(
        self,
        parties: Parties,
        gui_mode: GUIMode,
        parent: MainUI,
        controller: GameController,
        # gtp_conns: dict,
    ) -> None:
        super().__init__(parent=parent)
        self.parties = parties
        self.main_ui = parent
        self.controller = controller
        self._deco = None

        self.show_analyzed_variation = False
        self.stonesound = QSoundEffect()
        self.stonesound.setSource(
            QUrl.fromLocalFile(os.path.join(BASE_DIR, "gui/sounds/stone.wav"))
        )
        self._gui_mode = gui_mode
        self.initial_gui_mode = gui_mode
        self.boardwidget = BoardWidget(self, controller.ruleset.boardsize)
        self.boardoverlay = BoardOverlay(self)
        self.mode_change_listeners = []
        self.bar = BarWidget(self)
        self.ruleset = controller.ruleset
        self.bar.btn_settings.setFocus()
        self.receiver = GuiReceiver(game_ui=self)

    # def gameended_action(self, reason: str):
    #    msg = QMessageBox(self)
    #    msg.setIcon(QMessageBox.Information)
    #    msg.setText(reason)
    #    msg.show()

    @property
    def gui_mode(self):
        return self._gui_mode

    @gui_mode.setter
    def gui_mode(self, mode: GUIMode):
        self._gui_mode = mode
        for widget in self.mode_change_listeners:
            widget.mode_changed(mode)

    def _handle_rightclick(self, iwidget: IntersectionWidget):
        atype = self.annotation_type
        pos = iwidget.board_pos
        if self.gui_mode == GUIMode.EDIT and atype:
            assert self.last_turn
            annos = self.last_turn.node.annos
            found = False
            match atype:
                case "B" | "W":
                    # self.last_turn.node.annos.stones.pop(pos, None)
                    if found := self.last_turn.board.intersection(pos).color.name.startswith(atype):
                        self.controller.annotate(iwidget.board_pos, Color.EMPTY)
                case "TR" | "SQ" | "CR":
                    if annos.markers[pos].name == atype:
                        found = annos.markers.pop(pos, None)
                case "1":
                    found = annos.numbers.pop(pos, None)
                case "A":
                    found = annos.chars.pop(pos, None)
                case "AR":
                    for pospair in annos.arrows:
                        if pos in pospair:
                            found = True
                            break
                    if found:
                        annos.arrows.remove(pospair)

            if found:
                self.controller.rm_anno()
        # if atype in ("B", "W"):
        #    self.controller.annotate(iwidget.board_pos, Color.EMPTY)

    def inter_clicked(self, iwidget: IntersectionWidget, is_rightclick: bool):
        iwidget._hover = False
        if is_rightclick:
            self._handle_rightclick(iwidget)
        else:
            assert self.last_turn
            board = self.last_turn.board
            inter = board.intersection(iwidget.board_pos)
            pos = iwidget.board_pos
            if self.gui_mode == GUIMode.COUNT:
                if inter.color:
                    self.controller.toggle_status(iwidget.board_pos)
            elif self.annotation_type:
                val: str | Marker | Color | None = None
                end = None
                match self.annotation_type:
                    case "B":
                        val = Color.BLACK
                    case "W":
                        val = Color.WHITE
                    case "TR":
                        val = Marker.TR
                    case "SQ":
                        val = Marker.SQ
                    case "CR":
                        val = Marker.CR
                    case "1":
                        val = "1"
                    case "A":
                        val = "A"
                    case "AR" | "LN":
                        if self.boardoverlay.startpos:
                            end = pos
                            pos = self.boardoverlay.startpos
                            val = self.annotation_type
                        else:
                            self.boardoverlay.startpos = pos
                if val:
                    self.controller.annotate(pos=pos, name=val, end=end)
                    self.boardoverlay.startpos = None
            else:
                # self.boardwidget.show_analyzed_variation = False
                if isinstance(self.parties[color := self.last_turn.next_color], GUIPlayer):
                    self.controller.play(
                        color=color,
                        pos=iwidget.board_pos,
                    )

    def undo(self):
        self.gui_mode = self.initial_gui_mode
        self.controller.do_prev_stone()

    def open_as_new(self) -> None:
        ruleset = copy(self.ruleset)
        assert self.last_turn
        cpy = self.last_turn.node.as_copy()
        self.main_ui.add_game(
            mode=GUIMode.EDIT,
            ruleset=ruleset,
            cursor=cpy,
        )

    def resizeEvent(self, event):
        size = event.size()
        height = size.height()
        width = size.width()
        boardlength = min(height, width)
        self.boardwidget.resize(boardlength, boardlength)
        self.boardoverlay.resize(boardlength, boardlength)
        self.bar.setGeometry(boardlength, 0, width, height)
        self.bar.resize(width - boardlength, height)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        self.controller.quit()
        return super().closeEvent(event)
