#!/usr/bin/env python3

import sys

# support ctrl-c
import os
import signal

# global data_container
from libs.data_container import data_container as dc

# dc.config: config dict
# dc.module:

# dc.io_port = {}  # dc.io_port
from libs.IOWrapper.ioHelpers import IoPortsShelf

dc.io_port = IoPortsShelf()

# ?dc.logging: logging object
# ?dc.e: events object
# ?dc.hw: hardware dict


def get_git_version():
    """Get git hash rev of current HEAD, add suffix '-changed' when any tracked file is changed."""
    import subprocess

    try:
        # get unique version id: tag/HEAD, branch, steps away, hash  and dirty or not.
        version = (
            subprocess.check_output(["git", "describe", "--all", "--long", "--dirty"])
            .decode("ascii")
            .strip()
        )

    except Exception as e:
        version = "version-unknown"
        print(f"Warning: Could not read version from git: ({e})")

    return version


# set app name and version in envirement:
dc.app_name = "doorlockd-client"
dc.app_ver = get_git_version()
dc.app_name_ver = f"{dc.app_name}({dc.app_ver})"


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
# create formatter and add it to the handlers
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


# set logger level to lowest needed by our handlers:
logger.setLevel(min([h.level for h in logger.handlers]))
if dc.config.get("doorlockd", {}).get("log_level"):
    logger.warning(
        f"deprecated config used and will be ignored: doorlockd.log_level = {dc.config.get('doorlockd', {}).get('log_level')}"
    )
logger.debug(f"loglevels set: logger: {logger.level}, handlers: {logger.handlers}")

dc.logger = logger
dc.logger.info(f"{dc.app_name_ver} starting up...")


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
# exit -> dc.module.exit()
#
signal.signal(signal.SIGINT, lambda signal, frame: dc.module.exit("Exit: got sigint"))
signal.signal(signal.SIGTERM, lambda signal, frame: dc.module.exit("Exit: got sigterm"))


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

            # call main_loop, this will wait until exit/abort
            dc.module.main_loop()

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
