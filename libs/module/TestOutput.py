import libs.IOWrapper as IO
from libs.data_container import data_container as dc


class TestOutput:

    def __init__(self, config={}):
        # initialize myself
        self.io_output_name = config["io_output"]
        self.io_input_name = config["io_input"]

        # event
        self.event_name = config.get("event", "action_teo")

    def setup(self):
        # grab io_port from dc.io_port
        self.io_output = dc.io_port[self.io_output_name]
        self.io_input = dc.io_port[self.io_input_name]

    def enable(self):
        # enable module
        self.io_output.setup(IO.OUTPUT)
        self.io_input.setup(IO.INPUT)

        # event falling edge
        self.io_input.add_event_detect(
            IO.EDGE_RISING, lambda: dc.e.raise_event(self.event_name, {})
        )

        self.io_input.add_event_detect(
            IO.EDGE_FALLING, lambda: dc.logger.info("TEO: IO.EDGE_FALLING")
        )
        self.io_input.add_event_detect(
            IO.EDGE_RISING, lambda: dc.logger.info("TEO: IO.EDGE_RISING")
        )

        # connect event to our callback
        self.event = dc.e.subscribe(self.event_name, self.action_callback)

    def disable(self):
        # disable module
        # cancel event
        self.event.cancel()

        # set output low
        self.io_output.output(IO.LOW)

        # set ...
        self.io_input.remove_event_detect()

    def teardown(self):
        # de-setup module
        # cleanup ports
        self.io_input.cleanup()
        self.io_output.cleanup()

    def action_callback(self, data={}):

        # invert output
        self.io_output.output(not self.io_output.input())

        # log
        dc.logger.info(
            "TEO: action input={}, output={}".format(
                self.io_input.input(), self.io_output.input()
            )
        )
