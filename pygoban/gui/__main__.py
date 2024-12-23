import argparse
import logging
import sys

from PyQt5.QtCore import QSettings  # pylint: disable=no-name-in-module
from PyQt5.QtWidgets import QApplication, QWidget  # pylint: disable=no-name-in-module

from .settingsdialog import SettingsDialog


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("pygoban")
    parser.add_argument("sgf_path", nargs="?", default=None)
    parser.add_argument("-b", "--black-name", help="Black Name")
    parser.add_argument("-w", "--white-name", help="White Name")
    # parser.add_argument("--black-engine", help="Black GTP")
    # parser.add_argument("--white-engine", help="White GTP")
    parser.add_argument("--handicap", help="Handicap", type=int, default=0)
    parser.add_argument("-s", "--boardsize", help="Boardsize", type=int, default=19)
    parser.add_argument("--komi", help="komi", type=float)
    parser.add_argument(
        "--mode", help="Modus(play, edit)", choices=("PLAY", "EDIT"), default="PLAY"
    )
    parser.add_argument("--time", help="[maintime]:[byoyomi_time]:[byoyomi_num]:[byoyomi_stones]")
    return parser


def get_qsettings() -> QSettings:
    def defaults(groupname: str, data: dict):
        qsettings.beginGroup(groupname)
        for key, val in data.items():
            if (qval := qsettings.value(key)) is None:
                logging.debug("No value for '%s' in qsettings. Use default '%s'", key, val)
                qsettings.setValue(key, val)
            else:
                logging.debug("Value for '%s' from  qsettings: '%s'", key, qval)
        qsettings.endGroup()

    qsettings = QSettings("theithec", "pygoban")
    defaults("board", {"size": 19, "komi": 6.5, "handicap": 0})
    defaults("clock", {"main": 60 * 5, "byoyomi_time": 60, "byoyomi_num": 3, "byoyomi_stones": 1})
    defaults("players", {"black_name": "Black", "white_name": "White"})
    defaults("gtp", {"engines": {}})
    return qsettings


def merged_config():
    qsettings = get_qsettings()
    parser = get_argparser()
    argsdict = vars(parser.parse_args())
    argsdict["boardsize"] = int(argsdict["boardsize"] or qsettings.value("board/size"))
    argsdict["komi"] = float(argsdict["komi"] or qsettings.value("board/komi"))
    argsdict["handicap"] = int(argsdict["handicap"] or qsettings.value("board/handicap"))
    argsdict["gtp_engines"] = qsettings.value("gtp/engines")

    # print("M", qsettings.value("clock/main"))
    argsdict["time"] = ":".join(
        [
            str(qsettings.value(f"clock/{val}")) or "0"
            for val in ("main", "byoyomi_time", "byoyomi_num", "byoyomi_time")
        ]
    )
    logging.debug("Use settings %s", argsdict)
    return argsdict


app = QApplication(sys.argv)
parent = QWidget()
parent.settings = merged_config()
gw = SettingsDialog(parent=parent)
gw.show()

# Start the event loop.
app.exec()
