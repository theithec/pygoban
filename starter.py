from pygoban import Color, GameInfo, Member, Parties, Party, Ruleset
from pygoban.gui.gamewidget import GameWidget

info = GameInfo()
ruleset = Ruleset(boardsize=9, komi=0, handicap=0, info=info)
parties = Parties(
    black=Party(color=Color.BLACK, members=[Member(name=Color.BLACK.name)]),
    white=Party(color=Color.WHITE, members=[Member(name=Color.WHITE.name)]),
)
gw = GameWidget(
    parent=None,
    ruleset=ruleset,
    parties=parties,
)
gw.show()
