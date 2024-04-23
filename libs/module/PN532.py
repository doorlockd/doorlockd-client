import libs.Module as module
from libs.Events import State


import libs.IOWrapper as IO
from libs.data_container import data_container as dc

logger = dc.logger


import nfc

# from nfc.clf import RemoteTarget

import libs.IOWrapper.PN532
from libs.pn532gpio import pn532Gpio

from libs.tools import hwid2hexstr
import time
import threading


class PN532(module.BaseModule):

    def __init__(self, config={}):
        # initialize myself
        #
        super().__init__(config)
        # initilialize pn532
        # config path + device
        # usb[:vendor[:product]] / usb[:bus[:device]] / tty:port:driver / com:port:driver / udp[:host][:port]
        self.clf = nfc.ContactlessFrontend(config.get("path", "ttyS2:pn532"))

        # RFID
        if config.get("rfid_enabled", False):
            self.rfid = RfidReader(
                self.clf, self.events, config.get("rfid_event", "rfid_event")
            )

        #
        # GPIO, use pn532 hardware
        #
        self._gpio = pn532Gpio(self.clf)
        io_pn532 = IO.PN532.IOChip(self._gpio)
        # [module.pn532]
        # type = "PN532"
        # io_export.led1 		= { port = "p30", limit_direction = "OUTPUT" }
        # io_export.led2 		= { port = "p31", limit_direction = "OUTPUT" }
        # io_export.led3 		= { port = "p32", limit_direction = "OUTPUT" }
        # io_export.led4 		= { port = "p33", limit_direction = "OUTPUT" }
        # io_export.teo_out 	= { port = "p71", limit_direction = "OUTPUT", active_low = false }
        # io_export.teo_in  	= { port = "p72", limit_direction = "INPUT", active_low = false }

        for k in config["io_export"].keys():
            logger.info(
                "export io name: '%s', port: '%s' (limit_direction=%s, active_low=%s)",
                k,
                config["io_export"][k]["port"],
                config["io_export"][k].get("limit_direction", None),
                config["io_export"][k].get("active_low", False),
            )

            port = config["io_export"][k]["port"]

            limit_direction = config["io_export"][k].get("limit_direction", None)
            if limit_direction is not None:
                limit_direction = getattr(IO, limit_direction)

            active_low = config["io_export"][k].get("active_low", False)

            dc.io_port[k] = io_pn532.Port(
                port, limit_direction=limit_direction, active_low=active_low
            )

        # dc.io_port['p30'] = io_pn532.Port('p30')
        # dc.io_port['p31'] = io_pn532.Port('p31')
        # dc.io_port['p71'] = io_pn532.Port('p71')
        # dc.io_port['p72'] = io_pn532.Port('p72')

    def setup(self):
        # setup module
        pass

    def enable(self):
        # enable module
        self.rfid.start_thread()

        # # DEBUG GPIO
        # self._gpio.debug_event_detect()

    def disable(self):
        # disable module
        self.rfid.stop_thread()

    def teardown(self):
        # #de-setup module
        # # disable pn532 gpio
        # self._gpio.debug_event_detect()
        # self._gpio.debug_info()
        self._gpio.hw_exit()
        # # remove pn532
        self.clf.close()
        pass


class RfidReader:
    def __init__(self, clf, event_bus, event):
        self.clf = clf
        self.event_bus = event_bus
        self.event = event
        self.thread = None

        self.state_reader_ready = State()
        self.state_reader_ready.subscribe(
            lambda data: logger.debug(
                "PN532.rfid.state_reader_ready: %s|%s",
                str(data),
                str(self.state_reader_ready.value),
            )
        )

    def run(self):
        """threading run()"""
        logger.info("run detect loop started ({:s}).".format("PN532 RFiD Reader"))
        self.stop_loop = False

        while not self.stop_loop:
            self.state_reader_ready.value = True
            self.io_wait_for_tag_detected()
            self.state_reader_ready.value = False

    def io_wait_for_tag_detected(self):
        """start RFID reader and wait , callback_tag_detected() is run when a tag is detected."""

        targets = ["106A", "106B", "212F", "424F"]  # all supported by PN532
        target = self.clf.connect(
            rdwr={"on-connect": lambda tag: False, "iterations": 1, "targets": targets},
            terminate=lambda: self.stop_loop,
        )
        if target is False:
            # let's see how often this happens:
            # logger.info("clf.connect returned False, maybe lost connection.")
            raise Exception("clf.connect returned False, maybe lost connection.")
        elif target is not None:
            self.event_bus.raise_event(
                "rfid_comm_pulse"
            )  # when there is any RFID communication
            self.event_bus.raise_event(
                "rfid_comm_ready"
            )  # when there is any RFID communication
            logger.debug("HWID: " + str(target))

            self.callback_tag_detected(target)

    def callback_tag_detected(self, target):
        # print("DEBUG: ", target)
        # print("DEBUG: ", target.identifier)
        # print("DEBUG: ", hwid2hexstr(target.identifier))
        #
        hwid_str = hwid2hexstr(
            target.identifier
        )  # make hwid in hex lowercase string format

        if dc.rfid_auth.has_access(hwid_str):
            logger.info("hwid ({:s}) access alowed.".format(hwid_str))
            self.event_bus.raise_event(
                "rfid_access_allowed"
            )  # raise when rfid is access_allowed

            # global event:
            dc.e.raise_event(
                self.event, {}, wait=True
            )  # raise configured trigger_action for rfid_action

        else:
            logger.info("hwid ({:s}) access denied.".format(hwid_str))
            self.event_bus.raise_event(
                "rfid_access_denied"
            )  # raise when rfid is access_denied, will folow by ..._fin in x seconds
            time.sleep(3)
            self.event_bus.raise_event(
                "rfid_access_denied_fin"
            )  # raise when rfid is access_denied after sleeping x seconds.

    def start_thread(self):
        if not (self.thread and self.thread.is_alive()):
            self.thread = threading.Thread(target=self.run, args=())
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()  # Start the execution
            logger.info("start_thread {:s}".format("PN532 RFiD Reader"))

        else:
            logger.info(
                "notice: {:s}: start_thread, thread is already running ".format(
                    "PN532 RFiD Reader"
                )
            )

    def stop_thread(self):
        # stop the loop
        self.stop_loop = True
        logger.info("stop_thread {:s}".format("PN532 RFiD Reader"))

        # join thread to wait for stop:
        if self.thread:
            self.thread.join()
