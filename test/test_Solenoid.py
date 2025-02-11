import unittest
from .my_mocks import dc, MockGPIO, reset_data_container
from unittest.mock import MagicMock, Mock, call


solenoid_config = {"io_output": "GPIO01", "io_output_permanent_open_ui_led": "GPIO02"}
from libs.module.Solenoid import Solenoid

from .my_mocks import AssertDeltaTime


class TestSolenoid(unittest.TestCase):

    def setUp(self):
        # reset dc.e / dc.logger mocks
        reset_data_container()

        # create GPIO Mocks:
        self.mockIO01 = MockGPIO()
        self.mockIO02 = MockGPIO()

        dc.io_port["GPIO01"] = self.mockIO01
        dc.io_port["GPIO02"] = self.mockIO02

    def test_open_solenoid(self):
        """
        Testing 'open_solenoid' event
        > event 'open_solenoid'
        - is GPIO HIGH ?
        - validate GPIO calls

        > after wait_for(False) :
        - is GPIO LOW ?
        - validate GPIO calls

        - delta time should be ~ {time_wait} s

        """
        # 'time_wait': 0.1 is enough for running this test.
        time_wait = 0.1
        s1 = Solenoid({**solenoid_config, "time_wait": time_wait})
        s1.setup()
        s1.enable()

        # t_open start DeltaTime monitor
        t_open = AssertDeltaTime()
        dc.e.raise_event("open_solenoid")

        self.assertEqual(s1.state_open.value, True, "open_state should be True")
        self.mockIO01.assert_has_calls([call.setup(1), call.input(), call.output(1)])
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])

        # wait for solenoid close:
        s1.state_open.wait_for(False)
        t_open.end_timer()

        t_open.assertDeltaTime(time_wait, "Solenoid open took to long or short")
        self.assertEqual(s1.state_open.value, False, "open_state should be False")
        self.mockIO01.assert_has_calls(
            [call.setup(1), call.input(), call.output(1), call.output(0)]
        )
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])

    def test_cance_open_solenoid(self):
        """
        Testing 'cancel_open_solenoid' event
        > event 'open_solenoid'
        - is GPIO HIGH ?
        - validate GPIO calls

        > event 'cancel_open_solenoid'
        - is GPIO LOW ?
        - validate GPIO calls

        - delta time should be ~0s

        """
        # 'time_wait': 0.1 is enough for running this test.
        time_wait = 0.1
        s1 = Solenoid({**solenoid_config, "time_wait": time_wait})
        s1.setup()
        s1.enable()

        # t_start = time.monotonic()
        t_open = AssertDeltaTime()
        dc.e.raise_event("open_solenoid")

        self.assertEqual(s1.state_open.value, True, "open_state should be True")
        self.mockIO01.assert_has_calls([call.setup(1), call.input(), call.output(1)])
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])

        # close solenoid using event 'cancel_open_solenoid':
        dc.e.raise_event("cancel_open_solenoid")
        t_open.end_timer()

        t_open.assertDeltaTime(
            0, "imidiate cancel_open_solenoid open took to long or short"
        )
        self.assertEqual(s1.state_open.value, False, "open_state should be False")
        self.mockIO01.assert_has_calls(
            [call.setup(1), call.input(), call.output(1), call.output(0)]
        )
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])

    def test_allow_permanent_open_False(self):
        """
        Test allow_permanent_open = False

        > exec: toggle_permament_open_callback()
        - are GPIO LOW ?
        - validate GPIO calls

        > exec: toggle_permament_open_callback()
        - are GPIO LOW ?
        - validate GPIO calls


        """

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

        s1.toggle_permament_open_callback()
        self.assertEqual(
            s1.permanent_open_state.value, False, "permanent_open_state should be false"
        )
        self.assertEqual(s1.state_open.value, False, "open_state should be false")
        self.mockIO01.assert_has_calls([call.setup(1), call.input()])
        self.mockIO02.assert_has_calls([call.setup(1), call.output(0)])

    def test_allow_permanent_open_True(self):
        """
        > Test allow_permanent_open = True
          + listen to event 'toggle_permanent_open'

        > exec: toggle_permament_open_callback()
        - are GPIO HIGH ?
        - validate GPIO calls

        > event: 'toggle_permanent_open'
        - are GPIO LOW ?
        - validate GPIO calls
        """
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


if __name__ == "__main__":
    unittest.main()
