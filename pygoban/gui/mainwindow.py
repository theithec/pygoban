from PyQt6.QtGui import QCloseEvent, QIcon  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import QTabWidget  # pylint: disable=no-name-in-module

from pygoban import (
    Color,
    Game,
    GameInfo,
    MainGameController,
    Node,
    Parties,
    TimeSettings,
    rulesets,
)
from pygoban.sgf import reader

from . import BASE_DIR, MainUI, Settings
from .gamedialog import NewGameEditDialog, NewGamePlayDialog
from .gamewidget import GameWidget, GUIMode
from .players import GUIPlayer
from .settingsdialog import SettingsDialog
from .startwidget import StartWidget


class MainWindow(MainUI):
    def __init__(self, config: Settings):
        super().__init__()
        self.setWindowIcon(QIcon(f"{BASE_DIR}/gui/imgs/icon.png"))
        self.title = "Pygoban"
        self.setWindowTitle(self.title)
        self.setMinimumSize(1060, 600)
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.startwidget = StartWidget(manager=self)
        self.settings = config
        if not config.sgf_path:
            self.tabs.addTab(self.startwidget, "Welcome")
        else:
            self.load_sgf(config.sgf_path)
        self.setCentralWidget(self.tabs)

    def close_tab(self, index: int):
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if isinstance(widget, GameWidget):
            widget.close()

    def show_add_game_dialog(self):
        dlg = NewGamePlayDialog(self)
        dlg.show()

    def show_edit_board_dialog(self):
        dlg = NewGameEditDialog(self)
        dlg.show()

    def show_settings_dialog(self):
        dlg = SettingsDialog(self)
        dlg.show()

    def add_game(
        self, mode: GUIMode, ruleset: rulesets.BaseRuleset, cursor: Node | None = None
    ) -> MainGameController:
        game = Game(ruleset=ruleset)
        gamecontroller = MainGameController(game=game)
        parties = {
            color.name.lower(): GUIPlayer(color=color, name=ruleset.info.names[color], members=[])
            for color in (Color.BLACK, Color.WHITE)
        }
        gamewidget = GameWidget(
            parent=self,
            parties=Parties(**parties),
            gui_mode=mode,
            controller=gamecontroller,
        )
        self.tabs.addTab(gamewidget, ruleset.info.name)
        gamecontroller.start(receiver=gamewidget.receiver, node=cursor)
        if self.startwidget.isVisible():
            self.close_tab(0)
        self.tabs.setCurrentWidget(gamewidget)
        return gamecontroller

    def add_game_from_atomic_values(
        self,
        *,
        boardsize: int,
        komi: float,
        handicap: int,
        black_name: str,
        white_name: str,
        modestr: str,
        timestr: str,
        ruleset_name: str,
    ) -> MainGameController:
        mode: GUIMode = GUIMode[modestr]
        info = GameInfo(names={Color.BLACK: black_name, Color.WHITE: white_name})
        if timestr:
            timesettings = TimeSettings(*[int(part) for part in timestr.strip().split(":")])
        else:
            timesettings = None
        ruleset: rulesets.BaseRuleset = rulesets.by_key[rulesets.Key[ruleset_name]](
            boardsize=boardsize,
            komi=komi,
            handicap=handicap,
            info=info,
            timesettings=timesettings,
        )
        return self.add_game(mode=mode, ruleset=ruleset, cursor=None)

    def load_sgf(self, path: str):
        ruleset, cursor = reader.load(path)
        self.add_game(mode=GUIMode.EDIT, ruleset=ruleset, cursor=cursor)

    def closeEvent(self, event: QCloseEvent | None) -> None:  # pylint: disable=invalid-name
        for index in range(self.tabs.count()):
            self.close_tab(index)
        return super().closeEvent(event)
