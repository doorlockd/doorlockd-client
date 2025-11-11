import code
import readline
import rlcompleter
import os

import libs.IOWrapper as IO
from libs.data_container import data_container as dc
import libs.Module as module


class DebugREPL(module.BaseModule):

    def __init__(self, config: dict):
        # initialize myself
        self.histfile = os.path.join(os.path.expanduser("~"), ".doorlockd_repl_history")

        self.event = dc.e.subscribe("app_startup_complete", self.start_repl)

        self.console = None

    def setup(self):
        pass

    def enable(self):
        # enable module
        pass

    def start_repl(self, data):
        if not self.event.active():
            dc.logger.warning(
                "Debug REPL already started, or atleast local event already cleared."
            )
            return

        # clear event subscribtion so it can never be called twice.
        self.event.cancel()

        #
        # debug REPL:
        #

        try:
            readline.read_history_file(self.histfile)
            # default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        except PermissionError as e:
            dc.logger.warning(f"Could not open histfile ({self.histfile}): .{e}")

        # Detect libedit vs readline
        if "libedit" in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

        # setup console and start REPL
        self.console = code.InteractiveConsole(locals=globals())
        self.console.interact(banner="WARNING: Entering python interactive console..")

        # if not exiting yet, call exit:
        dc.module.exit("Exit python interactive console.")

    def disable(self):
        # disable module
        readline.write_history_file(self.histfile)

        if self.console:
            self.console.resetbuffer()
            self.console.runcode("quit()")
            self.console.resetbuffer()

        # clear event subscribtion so it can never be called twice.
        self.event.cancel()

    def teardown(self):
        # de-setup module
        pass
