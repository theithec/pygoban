# pylint: disable = redefined-outer-name, unused-argument
# from unittest.mock import Mock

import pytest
from PyQt6.QtWidgets import QApplication

from pygoban import (
    Color,
    Game,
    GameInfo,
    MainGameController,
    Parties,
    Pos,
    Settings,
    results,
)
from pygoban.gui import GUIMode
from pygoban.gui.gamewidget import GameWidget  # , GuiReceiver
from pygoban.gui.intersections import IntersectionWidget
from pygoban.gui.mainwindow import MainWindow
from pygoban.gui.players import GUIPlayer
from pygoban.receivers import BaseReceiver
from pygoban.rulesets import japanese


class TestReceiver(BaseReceiver):
    def __init__(self) -> None:
        super().__init__()
        self.events = set([results.TurnDone])

    def received_turn(self, result: results.TurnDone) -> None:
        pass


@pytest.fixture
def receiver():
    return TestReceiver()


@pytest.fixture
def qt_app():
    """Create QApplication for GUI tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qt_app):
    """Create MainWindow instance for testing"""
    settings = Settings()
    window = MainWindow(config=settings)
    return window


@pytest.fixture
def game_widget(main_window):
    """Create a GameWidget for testing"""
    ruleset = japanese.JapaneseRuleset(
        boardsize=9,
        komi=0.5,
        handicap=0,
        info=GameInfo(names={Color.BLACK: "Black", Color.WHITE: "White"}),
        timesettings=None,
    )
    game = Game(ruleset=ruleset)

    controller = MainGameController(game=game)
    parties = Parties(
        **{
            color.name.lower(): GUIPlayer(color=color, name=ruleset.info.names[color], members=[])
            for color in (Color.BLACK, Color.WHITE)
        }
    )
    game_widget = GameWidget(
        parties=parties, gui_mode=GUIMode.EDIT, parent=main_window, controller=controller
    )
    controller.start(game_widget.receiver)
    
    # Initialize last_turn with a basic TurnDone for testing
    # Create a temporary board for the test
    from pygoban.board import Board
    temp_board = Board(ruleset.boardsize)
    game_widget.last_turn = results.TurnDone(
        board=temp_board,
        node=game.nodes.root,
        next_color=Color.BLACK
    )
    
    return game_widget


@pytest.fixture
def inter_widget(game_widget):
    """Create an IntersectionWidget for testing"""
    # Create a mock boardwidget as parent
    from unittest.mock import Mock
    mock_parent = Mock()
    mock_parent.parent.return_value = game_widget
    return IntersectionWidget(parent=mock_parent, board_pos=Pos(0, 0), is_hoshi=False)
