import libs.Module as module
import libs.IOWrapper as IO
from libs.data_container import data_container as dc
import time
import threading


class Buzzer(module.BaseModule):

    def __init__(self, config: dict):
        super().__init__(config)

        # initialize myself
        self.io_output_name = config["io_output"]

        # event
        self.event_name = config.get("event", "buzz_buzzer")
        self.event = None

        self.melody = config.get("melody", "-... --.. --..")  # bzz

        # lock
        self.lock = threading.Lock()

    def setup(self):
        # grab io_port from dc.io_port
        self.io_output = dc.io_port[self.io_output_name]

    def enable(self):
        # enable module
        self.io_output.setup(IO.OUTPUT)

        # connect event to our callback
        self.event = dc.e.subscribe(self.event_name, self.action_callback)

    def disable(self):
        # disable module
        # cancel event
        if self.event:
            self.event.cancel()

        # set output low
        if hasattr(self, "io_output") and self.io_output.has_output:
            with self.lock:
                self.io_output.output(IO.LOW)

    def teardown(self):
        # de-setup module
        # cleanup ports
        if hasattr(self, "io_output"):
            self.io_output.cleanup()

    def action_callback(self, data: dict):
        # get lock
        if not self.lock.acquire(False):
            dc.logger.info("buzz buzzer ignored: (already buzzy)")

            ## wait
            # self.lock.acquire() and self.lock.release()
            return
        try:
            # log
            dc.logger.info("buzz buzzer (melody: '%s')", self.melody)

            # play notes:
            #  '.' = short
            #  '_' = long
            #  ' ' = pause
            for note in self.melody:
                if note == " ":
                    time.sleep(0.2)
                if note == "/":
                    time.sleep(0.5)
                if note == ".":
                    self.io_output.output(IO.HIGH)
                    time.sleep(0.1)
                    self.io_output.output(IO.LOW)
                    time.sleep(0.1)
                if note == "-":
                    self.io_output.output(IO.HIGH)
                    time.sleep(0.3)
                    self.io_output.output(IO.LOW)
                    time.sleep(0.1)
        finally:
            # release lock
            self.lock.release()
