# pylint: disable=import-outside-toplevel, global-statement
# because qt is optional, global is for QApp
import argparse
import logging
import sys
from typing import Any, Dict, Optional

from . import get_argparser, getconfig, InputMode
from .events import Counted, CursorChanged, Ended
from .status import Status, BLACK, WHITE
from .game import Game
from .player import Player, GTPPlayer
from .sgf.reader import parse
from .timesettings import TimeSettings
from .controller import ControllerMixin as _Controller

QAPP: Any = None
GAME_WINDOWS = []
"""No usage but avoiding garbage collection"""


def get_control_cls(nogui):
    if nogui:
        from .controller import ConsoleController as Controller
    else:
        from .gui.gamewindow import GameWindow as Controller
    print("C", Controller, nogui)
    return Controller


def get_player_cls(nogui):
    if nogui:
        from .player import ConsolePlayer as HumanPlayer
    else:
        from .gui.player import GuiPlayer as HumanPlayer
    return HumanPlayer


def initgame(
    controller_cls: _Controller,
    players: Dict[Status, Player],
    input_mode,
    boardsize=None,
    komi=None,
    root=None,
    nogui=False,
    sgf_file=None,
    handicap=None,
    time=None,
    extra_controller_kwargs: Optional[Dict] = None
    # **kwargs
):

    input_mode = (
        input_mode if isinstance(input_mode, InputMode) else InputMode[input_mode]
    )
    print("CK0", input_mode)
    config = getconfig()
    defaults = {
        "SZ": boardsize or int(config["PYGOBAN"]["boardsize"]),
        "KM": komi or config["PYGOBAN"]["komi"],
        "RU": "default",
        "PB": players[BLACK].name,
        "PW": players[WHITE].name,
        "GN": "-".join([players[col].name for col in (BLACK, WHITE)]),
    }
    if sgf_file:
        with open(sgf_file) as fileobj:
            sgftxt = fileobj.read()
            game = parse(sgftxt, defaults=defaults)
            for color, key in ((BLACK, "PB"), (WHITE, "PW")):
                players[color].name = game.infos.get(key, players[color].name)
    else:
        game = Game(HA=handicap, **defaults)

    controller_kwargs = dict(
        black=players[BLACK],
        white=players[WHITE],
        callbacks=game.get_callbacks(),
        infos=game.infos,
        input_mode=input_mode,
    )
    print("CK1", controller_kwargs["input_mode"])
    if time:
        timekwargs = dict(
            zip(
                ("maintime", "byoyomi_time", "byoyomi_num", "byoyomi_stones"),
                [int(arg) for arg in time.split(":")],
            )
        )
        controller_kwargs["timesettings"] = TimeSettings(**timekwargs)
    if extra_controller_kwargs:
        controller_kwargs.update(extra_controller_kwargs)
    print("CK2", controller_kwargs["input_mode"])
    controller = controller_cls(**controller_kwargs)
    game.add_listener(controller, [CursorChanged, Counted, Ended], wait=True)
    for col in (BLACK, WHITE):
        game.add_listener(players[col], [CursorChanged, Counted])
    if root:
        game.root = root

    if not nogui:
        controller.setMinimumSize(800, 600)
        controller.show()
        controller.activateWindow()
        GAME_WINDOWS.append(controller)

    return game, controller


def startgame(
    boardsize=None,
    komi=None,
    black_name=None,
    white_name=None,
    white_gtp=None,
    black_gtp=None,
    root=None,
    init_gui=False,
    nogui=False,
    sgf_file=None,
    handicap=None,
    time=None,
    mode=InputMode.PLAY,
    # **kwargs
):

    print("M0", mode)
    players = {}
    config = getconfig()
    player_cls = get_player_cls(nogui)
    for col, name, cmd in (
        (BLACK, black_name, black_gtp),
        (WHITE, white_name, white_gtp),
    ):
        if not cmd:
            players[col] = player_cls(col, name=name)
        else:
            players[col] = GTPPlayer(col, name=name or cmd, cmd=config["GTP"][cmd])
    game, controller = initgame(
        boardsize=boardsize,
        komi=komi,
        root=root,
        players=players,
        sgf_file=sgf_file,
        handicap=handicap,
        time=time,
        controller_cls=get_control_cls(nogui),
        input_mode=mode,
    )

    game.start()
    if init_gui:
        sys.exit(QAPP.exec_())

    # For testing
    return game, controller


def startpygoban():
    parser = get_argparser()
    args = parser.parse_args()
    args.mode = InputMode[args.mode]
    print("A", args.mode, dict(**vars(args)))
    if not args.nogui:
        from PyQt5.QtWidgets import QApplication

        global QAPP
        QAPP = QApplication([])
        if not any((args.sgf_file, args.boardsize, args.black_gtp, args.white_gtp)):
            from .gui.startwindow import StartWindow

            win = StartWindow(parser, starter_callback=startgame)
            win.show()
            print("VARS1", args)
            sys.exit(QAPP.exec_())
        startgame(**vars(args), init_gui=True)
    else:
        print("VARS2", args)
        startgame(**vars(args), init_gui=False)
