import os
import configparser
import sysconfig
import logging
logging.basicConfig(level=logging.INFO)


def writeconfig(config):
    configpath = os.path.sep.join((sysconfig.get_config_var("userbase"), ".pygoban.ini"))
    with open(configpath, "w") as configfile:
        config.write(configfile)


def getconfig():
    config = configparser.ConfigParser()
    config.read(os.path.sep.join((sysconfig.get_config_var("userbase"), ".pygoban.ini")))
    if not config.sections():
        config['PYGOBAN'] = {
            'boardsize': '19',
        }
        writeconfig(config)
    return config
