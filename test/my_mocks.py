import unittest

# mock dc.logger
from libs.data_container import data_container as dc
from unittest.mock import MagicMock, Mock, call

dc.logger = MagicMock()
from libs.Events import Events


class MockGPIO(MagicMock):
    """
    IOWrapper.IOPort Mock.

    compare calls:
    mock_gpio01.assert_has_calls([call.setup(1), call.input(), call.output(0), call.output(1)])

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = 0

    def setup(self, direction, *args, **kwargs):
        # direction
        # IO.INPUT = 0
        # IO.OUTPUT = 1
        self.has_input = True
        self.has_output = bool(direction)
        super().__getattr__("setup")(direction, *args, **kwargs)

    def input(self, *args, **kwargs):
        super().__getattr__("input")(*args, **kwargs)
        return self.value

    def output(self, value, *args, **kwargs):
        self.value = int(bool(value))  # make all value 1/0
        super().__getattr__("output")(self.value, *args, **kwargs)


def reset_data_container():
    # app dc. envirment:
    dc.logger = MagicMock()
    dc.io_port = {}
    # dc.e = MagicMock() # Events
    dc.e = Events()


reset_data_container()
