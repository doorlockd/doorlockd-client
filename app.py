#!/usr/bin/env python3

import sys

# support ctrl-c
import os
import signal

# global data_container
from libs.data_container import data_container as dc

# dc.config: config dict
# dc.module:
dc.io_port = {}  # dc.io_port
# ?dc.logging: logging object
# ?dc.e: events object
# ?dc.hw: hardware dict

import toml
import logging


# Read Config settings
try:
    dc.config = toml.load("config.ini")

except FileNotFoundError:
    sys.exit("Config file 'config.ini' is missing.")


#
# create logger with 'doorlockd'
#
logger = logging.getLogger()
logger.setLevel(dc.config.get("doorlockd", {}).get("log_level", "NOTSET"))
# create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s")

# console output on stderr
ch = logging.StreamHandler()
ch.setLevel(dc.config.get("doorlockd", {}).get("stderr_level", "INFO"))
ch.setFormatter(formatter)
logger.addHandler(ch)

# file output
if dc.config.get("doorlockd", {}).get("logfile_name"):
    logger.info(
        "logging to filename: {}, level: {}".format(
            dc.config.get("doorlockd", {}).get("logfile_name"),
            dc.config.get("doorlockd", {}).get("logfile_level", "INFO"),
        )
    )

    fh = logging.FileHandler(dc.config.get("doorlockd", {}).get("logfile_name"))
    fh.setLevel(dc.config.get("doorlockd", {}).get("logfile_level", "INFO"))
    fh.setFormatter(formatter)
    logger.addHandler(fh)


dc.logger = logger
dc.logger.info("doorlockd starting up...")


#
# events
#
from libs.Events import Events

dc.e = Events()


#
# Parse config modules:
#
# using importlib to dynamic load modules by name.
# config: ('nnn' = some unique name, 'xxx' = module file name)
# [module.nnn]
# type = "xxx"
from libs.Module import ModuleManager

dc.module = ModuleManager()


#
# set handle_excepthook to handle all uncaught exceptions in threads
#
def handle_excepthook(argv):
    dc.module.abort(f"Uncought exception caught with excepthook.", argv.exc_value)


import threading

threading.excepthook = handle_excepthook

#
# exit -> abort()
#
signal.signal(signal.SIGINT, lambda signal, frame: dc.module.abort("Exit: got sigint"))
signal.signal(
    signal.SIGTERM, lambda signal, frame: dc.module.abort("Exit: got sigterm")
)


#
# main loop
#
def main():

    if dc.config.get("doorlockd", {}).get("enable_modules", True):
        try:
            # initialize all modules
            dc.module.load_all(dc.config.get("module", {}))

            # setup all loaded modules
            dc.module.do_all("setup")

            # enable all loaded modules
            dc.module.do_all("enable")

            # we are up and running
            logger.info("doorlockd started.")

            # wait for abort_event
            dc.module.abort_event.wait()

        except Exception as e:
            logger.warning(e)

        # start exit
        dc.logger.info("start exit.")

        # disable all loaded modules
        dc.module.do_all("disable")

        # teardown all loaded modules
        dc.module.do_all("teardown")

        # done
        dc.logger.info("exit after proper shutdown.")


if __name__ == "__main__":
    main()
