import sys

from PyQt5.QtWidgets import QApplication

from pygoban import (
    BaseReceiver,
    Color,
    Game,
    GameController,
    GameInfo,
    Member,
    Parties,
    Party,
    Ruleset,
    TimeSettings,
)
from pygoban.gui import GUIMode
from pygoban.gui.gamewidget import GameWidget
from pygoban.gui.players import GUIPlayer

from pygoban.sgf import reader

ruleset, node = reader.load("/home/lotek/Dokumente/go/zoozu-MCHEN-2024-12-05.sgf")
# node = None

info = GameInfo()
# ruleset = Ruleset(boardsize=9, komi=7.5, handicap=0, info=info)  # , timesettings=TimeSettings())
parties = Parties(
    black=GUIPlayer(color=Color.BLACK, members=[Member(name=Color.BLACK.name)]),
    white=GUIPlayer(color=Color.WHITE, members=[Member(name=Color.WHITE.name)]),
)
game = Game(ruleset=ruleset)
controller = GameController(game=game)
app = QApplication(sys.argv)
gw = GameWidget(parent=None, controller=controller, parties=parties, gui_mode=GUIMode.EDIT)
controller.start(receiver=gw.receiver, node=node)
gw.show()

# Start the event loop.
app.exec()
