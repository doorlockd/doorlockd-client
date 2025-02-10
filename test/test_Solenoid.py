import unittest
from .my_mocks import dc, MockGPIO, reset_data_container
from unittest.mock import MagicMock, Mock, call


solenoid_config = {"io_output": "GPIO01", "io_output_permanent_open_ui_led": "GPIO02"}
from libs.module.Solenoid import Solenoid


class TestSolenoid(unittest.TestCase):

    def setUp(self):
        # reset dc.e / dc.logger mocks
        reset_data_container()

        # create GPIO Mocks:
        self.mockIO01 = MockGPIO()
        self.mockIO02 = MockGPIO()

        dc.io_port["GPIO01"] = self.mockIO01
        dc.io_port["GPIO02"] = self.mockIO02

    def test_allow_permanent_open_False(self):

        s1 = Solenoid(solenoid_config)
        s1.setup()
        s1.enable()

        s1.toggle_permament_open_callback()
        self.assertEqual(
            s1.permanent_open_state.value, False, "permanent_open_state should be false"
        )
        self.assertEqual(s1.state_open.value, False, "open_state should be false")
        self.mockIO01.assert_has_calls([call.setup(1), call.input()])
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])
        # print("mockIO01: ", self.mockIO01.method_calls)
        # print("mockIO02: ", self.mockIO02.method_calls)

        s1.toggle_permament_open_callback()
        self.assertEqual(
            s1.permanent_open_state.value, False, "permanent_open_state should be false"
        )
        self.assertEqual(s1.state_open.value, False, "open_state should be false")
        self.mockIO01.assert_has_calls([call.setup(1), call.input()])
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])
        # print("mockIO01: ", self.mockIO01.method_calls)
        # print("mockIO02: ", self.mockIO02.method_calls)

    def test_allow_permanent_open_True(self):
        s1 = Solenoid({**solenoid_config, **{"allow_permanent_open": True}})
        s1.setup()
        s1.enable()

        s1.toggle_permament_open_callback()
        self.assertEqual(
            s1.permanent_open_state.value, True, "permanent_open_state should be true"
        )
        self.assertEqual(s1.state_open.value, True, "open_state should be true")
        self.mockIO01.assert_has_calls([call.setup(1), call.input(), call.output(1)])
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0), call.output(1)])
        # print("mockIO01: ", self.mockIO01.method_calls)
        # print("mockIO02: ", self.mockIO02.method_calls)

        # s1.toggle_permament_open_callback()
        dc.e.raise_event("toggle_permanent_open")
        self.assertEqual(
            s1.permanent_open_state.value, False, "permanent_open_state should be false"
        )
        self.assertEqual(s1.state_open.value, False, "open_state should be false")
        self.mockIO01.assert_has_calls(
            [call.setup(1), call.input(), call.output(1), call.output(0)]
        )
        self.mockIO02.assert_has_calls(
            [call.setup(1), call.output(0), call.output(1), call.output(0)]
        )
        # print("mockIO01: ", self.mockIO01.method_calls)
        # print("mockIO02: ", self.mockIO02.method_calls)
        # print("dc.e:", dc.e.method_calls)
        # print("dc.logger:", dc.logger.method_calls)


if __name__ == "__main__":
    unittest.main()
