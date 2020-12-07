import configparser
import enum
from dataclasses import dataclass, field
from typing import Dict
import logging
import os
import sysconfig

logging.basicConfig(level=logging.INFO)


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


@dataclass
class Result:
    pass


@dataclass
class GameResult(Result):
    points: Dict = field(default_factory=dict)
    prisoners: Dict = field(default_factory=dict)


class InputMode(enum.Enum):
    PLAY = "PLAY"
    EDIT = "EDIT"
    COUNT = "COUNT"
    ENDED = "ENDED"


END_BY_TIME = "{color}+T"
END_BY_RESIGN = "{color}+R"
