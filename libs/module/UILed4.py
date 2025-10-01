import libs.Module as module
import libs.IOWrapper as IO
from libs.data_container import data_container as dc
import time

from libs.Events import State, Events


class LedMethods:
    def __init__(self, io_port):
        self.io_port = io_port

    def on(self):
        self.io_port.output(IO.HIGH)

    def off(self):
        self.io_port.output(IO.LOW)

    def blink(self, duration=0.05):
        self.on()
        time.sleep(duration)
        self.off()

    def short(self):
        self.blink(0.1)

    def medium(self):
        self.blink(0.3)

    def long(self):
        self.blink(0.6)

    def signal(self):
        """show signal for 2.x seconds."""
        self.on()
        time.sleep(0.6)
        self.off()
        time.sleep(0.3)
        self.on()
        time.sleep(0.6)
        self.off()
        time.sleep(0.3)
        self.on()
        time.sleep(0.6)
        self.off()


class UILed4(module.BaseModule):

    def __init__(self, config={}):
        super().__init__(config)

        # initialize myself
        self.led1_name = config["led1"]
        self.led2_name = config["led2"]
        self.led3_name = config["led3"]
        self.led4_name = config["led4"]

        self.mod_solenoid_name = config.get("solenoid", None)
        self.mod_rfid_name = config.get("rfid", None)
        self.blink_on_buttons = config.get("blink_on_buttons", [])

        # subscriptions to events/States
        self.s = []

    def setup(self):
        # grab io_port from dc.io_port
        self.io_led1 = dc.io_port[self.led1_name]
        self.io_led2 = dc.io_port[self.led2_name]
        self.io_led3 = dc.io_port[self.led3_name]
        self.io_led4 = dc.io_port[self.led4_name]

        # grab module from dc.module[]
        # if self.mod_solenoid_name is not None:
        self.mod_solenoid = dc.module.get(self.mod_solenoid_name, None)

        # if self.mod_rfid_name is not None:
        self.mod_rfid = dc.module.get(self.mod_rfid_name, None)

    def enable(self):
        # enable module
        self.io_led1.setup(IO.OUTPUT)
        self.io_led2.setup(IO.OUTPUT)
        self.io_led3.setup(IO.OUTPUT)
        self.io_led4.setup(IO.OUTPUT)

        self.led1 = LedMethods(self.io_led1)
        self.led2 = LedMethods(self.io_led2)
        self.led3 = LedMethods(self.io_led3)
        self.led4 = LedMethods(self.io_led4)

        # turn leds off on startup
        self.led1.off()
        self.led2.off()
        self.led3.off()
        self.led4.off()

        #
        # do some logic:
        #

        # for led3/red led = access denied and lock_disabled (if available)
        # overwrite off value with value of dc.rfid_auth.api.lock_disabled.value
        if hasattr(dc.rfid_auth, "api") and hasattr(dc.rfid_auth.api, "lock_disabled"):
            get_default_value_for_led3 = lambda: dc.rfid_auth.api.lock_disabled.value
        else:
            get_default_value_for_led3 = lambda: false

        # solenoid
        if self.mod_solenoid is not None:
            assert hasattr(self.mod_solenoid, "state_open") and isinstance(
                self.mod_solenoid.state_open, State
            ), "[ui4led] solenoid: configured module is not compatible. (state)"
            self.s.append(
                self.mod_solenoid.state_open.subscribe(
                    lambda value: self.io_led4.output(value)
                )
            )

        # RFID
        if self.mod_rfid is not None:
            assert hasattr(
                self.mod_rfid, "rfid"
            ), "[ui4led] rfid: configured module is not compatible. (.rfid)"
            assert hasattr(self.mod_rfid.rfid, "state_reader_ready") and isinstance(
                self.mod_rfid.rfid.state_reader_ready, State
            ), "[ui4led] rfid: configured module is not compatible. (rfid.state_reader_ready)"
            # assert hasattr(self.mod_rfid.rfid, "state_reader_ready") and isinstance(
            #     self.mod_rfid.rfid.api.lock_disabled, State
            # ), "[ui4led] rfid: configured module is not compatible. (rfid.api.lock_disabled)"
            assert hasattr(self.mod_rfid, "events") and isinstance(
                self.mod_rfid.events, Events
            ), "[ui4led] rfid: configured module is not compatible. (events)"

            events = self.mod_rfid.events
            self.s.append(
                self.mod_rfid.rfid.state_reader_ready.subscribe(
                    lambda v: self.io_led1.output(v)
                )
            )

            # api.lock_disabled: led3/red led on
            if hasattr(dc.rfid_auth, "api") and hasattr(
                dc.rfid_auth.api, "lock_disabled"
            ):
                self.s.append(
                    dc.rfid_auth.api.lock_disabled.subscribe(
                        lambda v: self.io_led3.output(
                            dc.rfid_auth.api.lock_disabled.value
                        )
                    )
                )

            self.s.append(
                events.subscribe("rfid_comm_pulse", lambda data: self.led2.blink())
            )
            self.s.append(
                events.subscribe("rfid_comm_ready", lambda data: self.led2.blink())
            )
            self.s.append(
                events.subscribe(
                    "rfid_comm_error",
                    lambda data: self.led3.blink()
                    or self.led2.blink()
                    or self.led3.blink()
                    or self.led2.blink(),
                )
            )
            self.s.append(
                events.subscribe("rfid_access_denied", lambda data: self.led3.on())
            )
            self.s.append(
                # events.subscribe("rfid_access_denied_fin", lambda data: self.led3.off())
                # revert red led to default value == lock_disabled
                events.subscribe(
                    "rfid_access_denied_fin",
                    lambda v: self.io_led3.output(get_default_value_for_led3()),
                )
            )

        # blink_on_buttons
        for btn in self.blink_on_buttons:
            mod = dc.module.get(btn, None)
            if mod is not None:
                assert hasattr(mod, "events") and isinstance(
                    mod.events, Events
                ), "[ui4led] {}: configured module is not compatible. (events)".format(
                    btn
                )
                dc.logger.info("UILed4 blink on button {} {}".format(btn, mod))
                self.s.append(
                    mod.events.subscribe("pressed", lambda data: self.led2.blink())
                )

    def disable(self):
        # disable module
        # cancel event

        # cleanup event/state subscriptions
        for s in self.s:
            s.cancel()

        # set output low
        if hasattr(self, "io_led1") and self.io_led1.has_output:
            self.io_led1.output(IO.LOW)
        if hasattr(self, "io_led2") and self.io_led2.has_output:
            self.io_led2.output(IO.LOW)
        if hasattr(self, "io_led3") and self.io_led3.has_output:
            self.io_led3.output(IO.LOW)
        if hasattr(self, "io_led4") and self.io_led4.has_output:
            self.io_led4.output(IO.LOW)

    def teardown(self):
        # de-setup module
        # cleanup ports
        if hasattr(self, "io_led1"):
            self.io_led1.cleanup()
        if hasattr(self, "io_led2"):
            self.io_led2.cleanup()
        if hasattr(self, "io_led3"):
            self.io_led3.cleanup()
        if hasattr(self, "io_led4"):
            self.io_led4.cleanup()
