import sys

from PyQt5.QtWidgets import QApplication

from pygoban import (
    Color,
    Game,
    GameController,
    GameInfo,
    Member,
    Parties,
    Ruleset,
    TimeSettings,
)
from pygoban.gui import GUIMode
from pygoban.gui.gamewidget import GameWidget
from pygoban.gui.players import GUIPlayer

from pygoban.sgf import reader

from pygoban.gtp import GTPController

# ruleset, node = reader.load("/home/lotek/Dokumente/go/zoozu-MCHEN-2024-12-05.sgf")
node = None

info = GameInfo()
ruleset = Ruleset(boardsize=19, komi=7.5, handicap=0, info=info)  # , timesettings=TimeSettings())
parties = Parties(
    black=GUIPlayer(color=Color.BLACK, members=[Member(name=Color.BLACK.name)]),
    white=GUIPlayer(color=Color.WHITE, members=[Member(name=Color.WHITE.name)]),
)
game = Game(ruleset=ruleset)
controller = GameController(game=game)
app = QApplication(sys.argv)
gw = GameWidget(parent=None, controller=controller, parties=parties, gui_mode=GUIMode.EDIT)
cmd_line = "/home/lotek/lib/katago-cuda/katago gtp -model /home/lotek/.local/pipx/venvs/katrain/lib/python3.12/site-packages/katrain/models/kata1-b18c384nbt-s9996604416-d4316597426.bin.gz"
kata = GTPController(cmd_line=cmd_line, game=game)
# kata.set_action(Color.BLACK.name, True)
kata.set_action("analyze", True)
controller.add_receiver(kata)
controller.start(receiver=gw.receiver, node=node)
gw.show()

# Start the event loop.
app.exec()
