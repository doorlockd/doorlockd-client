import libs.Module as module
import libs.IOWrapper as IO
from libs.data_container import data_container as dc
from libs.Events import State


class Solenoid(module.BaseModule):
    state_vars = ["state_open"]

    def __init__(self, config={}):
        super().__init__(config)

        # initialize myself
        self.io_output_name = config["io_output"]

        # event
        self.event_name = config.get("event", "open_solenoid")
        self.cancel_event_name = config.get("cancel_event", "cancel_open_solenoid")

        self.time_wait = float(config.get("time_wait", 2.4))
        self.cancel_open_solenoid_delay = float(
            config.get("cancel_open_solenoid_delay", 0)
        )

        self.state_open = State(value=False)

        # permanent open:
        self.allow_permanent_open = bool(config.get("allow_permanent_open", False))
        self.event_name_toggle_permanent_open = str(
            config.get("event_toggle_permanent_open", "toggle_permanent_open")
        )
        self.permanent_open_state = State(value=False)
        self.io_output_name_permanent_open_ui_led = config.get(
            "io_output_permanent_open_ui_led", None
        )

        # set exit state of solenoid
        self.exit_state = bool(config.get("exit_state", False))

        self.event = None
        self.event_toggle_permanent_open = None

    def setup(self):
        # grab io_port from dc.io_port
        self.io_output = dc.io_port[self.io_output_name]

        # if not None
        if self.io_output_name_permanent_open_ui_led:
            self.io_output_permanent_open_ui_led = dc.io_port[
                self.io_output_name_permanent_open_ui_led
            ]

    def enable(self):
        # enable module
        self.io_output.setup(IO.OUTPUT)

        if self.io_output.input():
            # note, some GPIO libs will pull value LOW on setup. this message is here just incase we catch this:
            self.io_output.output(IO.LOW)
            dc.logger.warning(
                "!!! Solenoid was open on startup (this might show up by error)) !!!, io_output=%s",
                self.io_output_name,
            )

        # connect IO port to our state value
        # self.state_open = False -> self.io_output.output(IO.LOW)
        # self.state_open = True  -> self.io_output.output(IO.HIGH)
        self.state_open.set_logic(lambda v: bool(self.io_output.output(v) or v))

        # connect event to our open callback
        self.event_open = dc.e.subscribe(self.event_name, self.action_open_callback)
        # connect event to our cancel open callback
        self.event_cancel_open = dc.e.subscribe(
            self.cancel_event_name, self.action_cancel_open_callback
        )

        # permanent_open: connect event to our callback
        self.event_toggle_permanent_open = dc.e.subscribe(
            self.event_name_toggle_permanent_open, self.toggle_permament_open_callback
        )

        # permanent_open ui_led
        if hasattr(self, "io_output_permanent_open_ui_led"):
            self.io_output_permanent_open_ui_led.setup(IO.OUTPUT)
            self.io_output_permanent_open_ui_led.output(IO.LOW)

    def disable(self):
        # disable module

        # cancel event if exists
        for event in ["event_open", "event_cancel_open", "event_toggle_permanent_open"]:
            if hasattr(self, event) and getattr(self, event):
                getattr(self, event).cancel()

        # set output low
        self.state_open.value = False

        # cancel state logic:
        self.state_open.set_logic(None)

        if hasattr(self, "io_output") and self.io_output.has_output:
            self.io_output.output(self.exit_state)
            dc.logger.info(f"set solenoid exit state ({self.exit_state})")

        if (
            hasattr(self, "io_output_permanent_open_ui_led")
            and self.io_output_permanent_open_ui_led.has_output
        ):
            self.io_output_permanent_open_ui_led.output(IO.LOW)

    def teardown(self):
        # de-setup module

        # cleanup ports
        if hasattr(self, "io_output"):
            self.io_output.cleanup()

        if hasattr(self, "io_output_permanent_open_ui_led"):
            self.io_output_permanent_open_ui_led.cleanup()

    def action_open_callback(self, data={}):
        """
        Open Solenoid for self.time_wait seconds.
        """
        if self.permanent_open_state.value:
            dc.logger.info("open solenoid ignored: (permanent open)")
            self.state_open.wait_for(
                False, self.time_wait
            )  # block this thread for x seconds or when solenoid is closed
            return

        if self.state_open.value:
            dc.logger.info("open solenoid ignored: (already open)")
            self.state_open.wait_for(
                False
            )  # block this thread until solenoid is closed
            return

        # Open solenoid for x seconds:
        dc.logger.info("open solenoid (time_wait: %.2f seconds)", self.time_wait)
        # open solenoid
        self.state_open.value = True
        # wait time wait. or when solenoid open is canceled
        self.state_open.wait_for(False, self.time_wait)
        # close solenoid or return to permanent state.
        self.state_open.value = self.permanent_open_state.value

    def action_cancel_open_callback(self, data={}):
        """
        Cancel Open Solenoid.
        """
        # close solenoid or return to permanent state.
        if self.state_open.value:
            if self.cancel_open_solenoid_delay != 0:
                dc.logger.info(
                    f"cancel open solenoid. cancel_open_solenoid_delay = {self.cancel_open_solenoid_delay}"
                )
                # wait time wait. unless solenoid open is closed
                self.state_open.wait_for(False, self.cancel_open_solenoid_delay)

        dc.logger.info(
            f"cancel open solenoid. state_open = {self.state_open.value}, permanent_open_state = {self.permanent_open_state.value}"
        )
        if self.state_open.value:
            self.state_open.value = self.permanent_open_state.value

    def toggle_permament_open_callback(self, data={}):
        # only switch config setting on if your hardware supports pemanent_open:
        if not self.allow_permanent_open:
            dc.logger.warn(
                "allow_permanent_open disabled: toggle permanent open/close is disabled."
            )
            return

        # switch state:
        self.permanent_open_state.value = not self.permanent_open_state.value
        dc.logger.info(
            f"permanent_open_state switched to {self.permanent_open_state.value}."
        )

        # set UI LED if defined
        if (
            hasattr(self, "io_output_permanent_open_ui_led")
            and self.io_output_permanent_open_ui_led.has_output
        ):
            self.io_output_permanent_open_ui_led.output(self.permanent_open_state.value)

        # sync hardware:
        self.state_open.value = self.permanent_open_state.value
        dc.logger.info(
            f"hardware synced to new permanent_state {self.state_open.value}."
        )
