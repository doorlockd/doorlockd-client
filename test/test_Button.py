import unittest
from .my_mocks import dc, MockGPIO, reset_data_container
from unittest.mock import MagicMock, Mock, call


button_config = {"io_input": "GPIO01"}
from libs.module.Button import Button


class TestButton(unittest.TestCase):

    def setUp(self):
        # reset dc.e / dc.logger mocks
        reset_data_container()

        # create GPIO Mocks:
        self.mockIO01 = MockGPIO(value=1)
        dc.io_port["GPIO01"] = self.mockIO01

        dc.e = MagicMock()

    def test_Button_io_edge_detect(self):

        b1 = Button(button_config)
        b1.setup()
        b1.enable()

        # mocking EDGE_FALLING detect
        self.mockIO01.mock_change_input(0, 1)

        # excpecting event "button_pressed"
        dc.e.assert_has_calls([call.raise_event("button_pressed", {})])

        # expect setup + add_event_detect
        self.mockIO01.assert_has_calls(
            [
                call.setup(0),
                call.add_event_detect(0, "callback_fn"),
                call.mock_change_input(0, 1),
            ]
        )

        # print("dc.e", dc.e.method_calls)
        # print("mockIO01: ", self.mockIO01.method_calls)

    def test_Button_event_name(self):

        b1 = Button({**button_config, **{"event": "random_other_name"}})
        b1.setup()
        b1.enable()

        # mocking EDGE_FALLING detect
        self.mockIO01.mock_change_input(0, 1)

        # excpecting event "button_pressed"
        dc.e.assert_has_calls([call.raise_event("random_other_name", {})])

        # expect setup + add_event_detect
        self.mockIO01.assert_has_calls(
            [
                call.setup(0),
                call.add_event_detect(0, "callback_fn"),
                call.mock_change_input(0, 1),
            ]
        )

        # print("dc.e", dc.e.method_calls)
        # print("mockIO01: ", self.mockIO01.method_calls)


if __name__ == "__main__":
    unittest.main()
