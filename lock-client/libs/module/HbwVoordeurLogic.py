import libs.IOWrapper as IO
from libs.data_container import data_container as dc
from libs.Events import State

logger = dc.logger
# import logging
# logger = logging.getLogger(__name__)


#
# functie 1: Warschuwings LED op nachtslot schootdetectie.
# 			- io ui_door_open_detect
# 			- connect State / connect events 'door_opened','door_closed',
#
# functie 2: Blink Deur-open-knop verlichting bij verkeerd gebruik.
# 	 		- dagslotschootdetectie && !solenoid : blink deur-open-knop backlight.
#
# functie 3: raise cancel_open_solenoid event na nachtslot schoot detectie (deur gaat direct weer op slot.)
# 			- nachtslot schoot detectie : raise event ('door_opened')
# 			- connect event 'door_opened' to 'cancel_open_solenoid' event after x seconds.
#
# 		config: enable_cancelopensolenoid_on_dooropened = True
#
# functie 4: (future) open slot door dagslot schoot detectie + permanent open status.


class HbwVoordeurLogic:
    state_vars = ["state_dagslotschootdetectie", "state_nachtslotschootdetectie"]

    def __init__(self, config={}):
        # initialize myself
        self.io_dagslotschootdetectie_name = config.get(
            "io_dagslotschootdetectie", False
        )
        self.io_nachtslotschootdetectie_name = config.get(
            "io_nachtslotschootdetectie", False
        )
        self.io_ui_nachtslotschootnotificatie_open_name = config.get(
            "io_ui_nachtslotschootnotificatie_open", False
        )
        self.io_ui_nachtslotschootnotificatie_close_name = config.get(
            "io_ui_nachtslotschootnotificatie_close", False
        )
        self.io_ui_deuropenknopbacklight_name = config.get(
            "io_ui_deuropenknopbacklight", False
        )

        # # external events:
        # self.event_open_solenoid  = config.get('event_open_solenoid', 'open_solenoid')
        self.event_cancel_open_solenoid = config.get(
            "event_cancel_open_solenoid", "cancel_open_solenoid"
        )

        # state values:
        self.state_dagslotschootdetectie = State()
        self.state_nachtslotschootdetectie = State()

        self.state_dagslotschootdetectie.subscribe(
            lambda v: logger.info(f"state_dagslotschootdetectie = {v}")
        )
        self.state_nachtslotschootdetectie.subscribe(
            lambda v: logger.info(f"state_nachtslotschootdetectie = {v}")
        )

        # solenoid name
        self.solenoid_name = config.get("solenoid_name")
        self.solenoid = None

        # emitting events:
        self.event_door_opened_name = config.get("event_door_opened", "door_opened")
        self.event_door_closed_name = config.get("event_door_closed", "door_closed")
        self.event_doorhandle_opened_name = config.get(
            "event_doorhandle_opened", "doorhandle_opened"
        )
        # self.event_doorhandle_closed_name = config.get('event_doorhandle_closed', 'doorhandle_closed')

        # options:
        self.enable_cancelopensolenoid_on_dooropened = config.get(
            "enable_cancelopensolenoid_on_dooropened", True
        )

    def setup(self):
        # grab io_port from dc.io_port or set None when name is not defined.
        self.io_dagslotschootdetectie = (
            dc.io_port[self.io_dagslotschootdetectie_name]
            if self.io_dagslotschootdetectie_name
            else None
        )
        self.io_nachtslotschootdetectie = (
            dc.io_port[self.io_nachtslotschootdetectie_name]
            if self.io_nachtslotschootdetectie_name
            else None
        )
        self.io_ui_nachtslotschootnotificatie_open = (
            dc.io_port[self.io_ui_nachtslotschootnotificatie_open_name]
            if self.io_ui_nachtslotschootnotificatie_open_name
            else None
        )
        self.io_ui_nachtslotschootnotificatie_close = (
            dc.io_port[self.io_ui_nachtslotschootnotificatie_close_name]
            if self.io_ui_nachtslotschootnotificatie_close_name
            else None
        )
        self.io_ui_deuropenknopbacklight = (
            dc.io_port[self.io_ui_deuropenknopbacklight_name]
            if self.io_ui_deuropenknopbacklight_name
            else None
        )

        # grab module by name
        self.solenoid = dc.module.get(self.solenoid_name)

    def enable(self):
        # enable module

        #
        # init INPUT nachtslot schootdetectie edge detect : event door_opened / door_closed
        #
        if self.io_nachtslotschootdetectie:
            self.io_nachtslotschootdetectie.setup(IO.INPUT)
            self.state_nachtslotschootdetectie.set(
                self.io_nachtslotschootdetectie.input()
            )  # set initial value , better to do after setting edge_events, but this works for now.

            self.io_nachtslotschootdetectie.add_event_detect(
                IO.EDGE_FALLING, lambda: dc.e.raise_event(self.event_door_opened_name)
            )
            # self.io_nachtslotschootdetectie.add_event_detect(IO.EDGE_FALLING, lambda : dc.e.raise_event(self.event_door_closed_name) )
            logger.info(
                f"nachtslotschootdetectie on '{self.io_nachtslotschootdetectie_name}' enabled, emiting event '{self.event_door_opened_name}'/'{self.event_door_closed_name}'"
            )
            self.io_nachtslotschootdetectie.add_event_detect(
                IO.EDGE_RISING, lambda: self.state_nachtslotschootdetectie.set(True)
            )
            self.io_nachtslotschootdetectie.add_event_detect(
                IO.EDGE_FALLING, lambda: self.state_nachtslotschootdetectie.set(False)
            )
            # self.state_nachtslotschootdetectie.set(self.io_nachtslotschootdetectie.input()) # RequestReleasedError()
            logger.info(
                f"nachtslotschootdetectie on '{self.io_nachtslotschootdetectie_name}' enabled, On self.state_nachtslotschootdetectie"
            )

        #
        # init INPUT dagslot schootdetectie edge detect: event doorhandle_opened / doorhandle_closed
        #
        if self.io_dagslotschootdetectie:
            self.io_dagslotschootdetectie.setup(IO.INPUT)
            self.state_dagslotschootdetectie.set(
                self.io_dagslotschootdetectie.input()
            )  # set initial value , better to do after setting edge_events, but this works for now.

            # self.io_dagslotschootdetectie.add_event_detect(IO.EDGE_RISING,  lambda : dc.e.raise_event(self.event_doorhandle_opened_name) )
            # self.io_dagslotschootdetectie.add_event_detect(IO.EDGE_FALLING, lambda : dc.e.raise_event(self.event_doorhandle_closed_name) )
            # logger.info(f"dagslotschootdetectie on '{self.io_dagslotschootdetectie_name}' enabled, emiting events '{self.event_doorhandle_opened_name}'/'{self.event_doorhandle_closed_name}'")

            self.io_dagslotschootdetectie.add_event_detect(
                IO.EDGE_RISING, lambda: self.state_dagslotschootdetectie.set(True)
            )
            self.io_dagslotschootdetectie.add_event_detect(
                IO.EDGE_FALLING, lambda: self.state_dagslotschootdetectie.set(False)
            )
            # self.state_dagslotschootdetectie.set(self.io_dagslotschootdetectie.input()) # RequestReleasedError()
            logger.info(
                f"dagslotschootdetectie on '{self.io_dagslotschootdetectie_name}' enabled, On self.state_dagslotschootdetectie"
            )

        #
        # init Outputs
        #
        if self.io_ui_nachtslotschootnotificatie_open:
            self.io_ui_nachtslotschootnotificatie_open.setup(IO.OUTPUT)
        if self.io_ui_nachtslotschootnotificatie_close:
            self.io_ui_nachtslotschootnotificatie_close.setup(IO.OUTPUT)
        if self.io_ui_deuropenknopbacklight:
            self.io_ui_deuropenknopbacklight.setup(IO.OUTPUT)

        #
        # functie 1: Warschuwings LED op nachtslot schootdetectie.
        #
        if self.io_ui_nachtslotschootnotificatie_open:
            self.state_nachtslotschootdetectie.subscribe(
                lambda v: self.io_ui_nachtslotschootnotificatie_open.output(not v)
            )
            logger.info(
                f"ui_nachtslotschootnotificatie_open enabled on '{self.io_ui_nachtslotschootnotificatie_open_name}'."
            )
        if self.io_ui_nachtslotschootnotificatie_close:
            self.state_nachtslotschootdetectie.subscribe(
                lambda v: self.io_ui_nachtslotschootnotificatie_close.output(v)
            )
            logger.info(
                f"ui_nachtslotschootnotificatie_close enabled on '{self.io_ui_nachtslotschootnotificatie_close_name}'."
            )

        #
        # functie 2: Blink Deur-open-knop verlichting bij verkeerd gebruik.
        #
        if self.io_ui_deuropenknopbacklight:
            # idee voor later: eventueel als# !dagslotschootdetectie => notificatie aan
            # self.io_dagslotschootdetectie.add_event_detect(IO.EDGE_RISING,  lambda : self.io_ui_deuropenknopbacklight.output(IO.LOW) )
            # self.io_dagslotschootdetectie.add_event_detect(IO.EDGE_FALLING, lambda : self.io_ui_deuropenknopbacklight.output(IO.HIGH) )
            # not handle bar detect = True && not solenoid open = True
            self.state_dagslotschootdetectie.subscribe(
                lambda v: self.io_ui_deuropenknopbacklight.output(
                    not v and (not self.solenoid.state_open.value)
                )
            )

            # Alwaus turn off LED when Solenoid opens:
            self.solenoid.state_open.subscribe(
                lambda v: self.io_ui_deuropenknopbacklight.output(IO.LOW) if v else None
            )

            logger.info(
                f"ui_deuropenknopbacklight enabled on '{self.io_ui_deuropenknopbacklight_name}'."
            )

        #
        # functie 3: raise cancel_open_solenoid event na nachtslot schoot detectie (deur gaat direct weer op slot.)
        #
        if self.enable_cancelopensolenoid_on_dooropened:
            # connect event to our open callback
            self.subscription_dooropened_cancelsolenoid = dc.e.subscribe(
                self.event_door_opened_name,
                lambda d: dc.e.raise_event(self.event_cancel_open_solenoid),
            )
            logger.info(f"cancel_open_solenoid on door_opened enabled.")

    def disable(self):
        # disable module
        # cancel event
        if self.enable_cancelopensolenoid_on_dooropened:
            self.subscription_dooropened_cancelsolenoid.cancel()

        # set output low
        if self.io_ui_nachtslotschootnotificatie_open:
            self.io_ui_nachtslotschootnotificatie_open.output(IO.LOW)
        if self.io_ui_nachtslotschootnotificatie_close:
            self.io_ui_nachtslotschootnotificatie_close.output(IO.LOW)

        # remove event_detect
        if self.io_nachtslotschootdetectie:
            self.io_nachtslotschootdetectie.remove_event_detect()

    def teardown(self):
        # de-setup module
        # cleanup ports
        if self.io_dagslotschootdetectie:
            self.io_dagslotschootdetectie.cleanup()
        if self.io_nachtslotschootdetectie:
            self.io_nachtslotschootdetectie.cleanup()
        if self.io_ui_nachtslotschootnotificatie_open:
            self.io_ui_nachtslotschootnotificatie_open.cleanup()
        if self.io_ui_nachtslotschootnotificatie_close:
            self.io_ui_nachtslotschootnotificatie_close.cleanup()
        if self.io_ui_deuropenknopbacklight:
            self.io_ui_deuropenknopbacklight.cleanup()
