import argparse
import configparser
from collections import namedtuple
import enum
from dataclasses import dataclass, field
import signal
from typing import Dict
import logging
import os
import sysconfig

logging.basicConfig(level=logging.DEBUG)

signal.signal(signal.SIGINT, signal.SIG_DFL)  # kill with <Ctrl-C>


def writeconfig(config):
    configpath = os.path.sep.join((sysconfig.get_config_var("userbase"), "pygoban.ini"))
    with open(configpath, "w") as configfile:
        config.write(configfile)


def getconfig():
    config = configparser.ConfigParser()
    config.read(os.path.sep.join((sysconfig.get_config_var("userbase"), "pygoban.ini")))
    if not config.sections():
        config["PYGOBAN"] = {"boardsize": "19", "komi": 7.5}
        config["GTP"] = {}
        writeconfig(config)
    return config


Pos = namedtuple("Pos", ["x", "y"])


@dataclass
class Result:
    pass


@dataclass
class GameResult(Result):
    points: Dict = field(default_factory=dict)
    prisoners: Dict = field(default_factory=dict)
    msg: str = ""  # {color}+%s"


class InputMode(enum.Enum):
    PLAY = "PLAY"
    EDIT = "EDIT"
    COUNT = "COUNT"
    ENDED = "ENDED"


END_BY_TIME = "{color}+T"
END_BY_RESIGN = "{color}+R"


def get_argparser():
    parser = argparse.ArgumentParser("pygoban")
    parser.add_argument("sgf_file", nargs="?", default=None)
    parser.add_argument("--nogui", action="store_true", help="Show GUI")
    parser.add_argument("--komi", help="komi", type=float)
    parser.add_argument("--black-name", help="Black Name")
    parser.add_argument("--white-name", help="White Name")
    parser.add_argument("--black-gtp", help="Black GTP")
    parser.add_argument("--white-gtp", help="White GTP")
    parser.add_argument("--handicap", help="Handicap", type=int, default=0)
    parser.add_argument("--boardsize", help="Handicap", type=int)
    parser.add_argument(
        "--mode", help="Modus(play, edit)", choices=("PLAY", "EDIT"), default="PLAY"
    )
    parser.add_argument(
        "--time", help="[maintime]:[byoyomi_time]:[byoyomi_num]:[byoyomi_stones]"
    )
    return parser
