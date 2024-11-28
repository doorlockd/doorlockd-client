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

import datetime


class TargetGoneWhileReadingError(Exception):
    pass


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
        hwid_str = hwid2hexstr(
            target.identifier
        )  # make hwid in hex lowercase string format

        try:
            has_access = dc.rfid_auth.has_access(
                hwid_str, target=target, nfc_tools=NfcTools(target)
            )
        except TargetGoneWhileReadingError:
            has_access = None

        if has_access is True:
            logger.info("hwid ({:s}) access alowed.".format(hwid_str))
            self.event_bus.raise_event(
                "rfid_access_allowed"
            )  # raise when rfid is access_allowed

            # global event:
            dc.e.raise_event(
                self.event, {}, wait=True
            )  # raise configured trigger_action for rfid_action

        elif has_access is False:
            logger.info("hwid ({:s}) access denied.".format(hwid_str))
            self.event_bus.raise_event(
                "rfid_access_denied"
            )  # raise when rfid is access_denied, will folow by ..._fin in x seconds
            time.sleep(3)
            self.event_bus.raise_event(
                "rfid_access_denied_fin"
            )  # raise when rfid is access_denied after sleeping x seconds.

        else:
            # has_access is None or anythng else
            logger.info("hwid ({:s}) gone while reading.".format(hwid_str))
            time.sleep(2)

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


class NfcTools:
    """Set of tools to communicate with nfc tags or collect various tag data."""

    def __init__(self, target):
        self.target = target

    def _authenticate(
        self, secret=bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0]), page=0, timeout=0.005
    ):
        """Mifare classic / Type2Tag authentication implementation (not yet implemented in nfc module)"""

        # only for target.type Type2Tag
        if self.target.type != "Type2Tag":
            raise Exception("authenticate only for for type Type2Tag")

        # type2tag uses 0x60 for authentication.
        send = bytearray([0x60, page]) + secret + self.target._nfcid
        logger.debug(f"authenticate using: target.transceive({send.hex()}, {timeout})")
        # target.transceive(send, timeout)
        with self.target.clf.lock:
            return self.target.clf.device.chipset.in_data_exchange(send, timeout)

    def _read(self, page, max_retries=3):
        """wrapper for target.read(page), but then with retries for timeout
        Type2TagCommandError(nfc.tag.TIMEOUT_ERROR)
        """
        n = 0
        while n != max_retries:
            n = n + 1
            try:
                logger.debug(
                    f"attemp..... while read({page}), attemp ({n}/{max_retries})"
                )
                return self.target.read(page)
            except nfc.tag.tt2.Type2TagCommandError as e:
                if repr(e) != repr(
                    nfc.tag.tt2.Type2TagCommandError(nfc.tag.TIMEOUT_ERROR)
                ):
                    raise (e)
                else:
                    logger.debug(
                        f"TIMEOUT_ERROR while read({page}), attemp ({n}/{max_retries})"
                    )

        # max_retries reached, raise timeout error:
        # raise nfc.tag.tt2.Type2TagCommandError(nfc.tag.TIMEOUT_ERROR)
        raise TargetGoneWhileReadingError

        # TODO: how to respond here?, raise exception and ignore this NFC comunication like it never happened ? or add this message to the meta dict so the hwid still showsup as "UnknownKey".
        # Idea TargetGoneWhileReadingError:
        # - UI Leds keep shows something stuck in communication , so that enduser whill understand he/she needs to keep the rfid tag longer in front of the reading device to succeed reading.
        # we raise this exception anywhere in the dc.rfid_auth.has_access() callback
        # raise TargetGoneWhileReadingError

    def parse_ovchipkaart(self, data):
        """Parse NL OV-Chipkaart, we now only read validuntil date."""

        def getbits(data, start, end):
            """Return number at bit positions of bytestring data (msb first)"""
            val = 0
            # verbose = (start == 4 and end == 6)
            for byte in range(start // 8, (end + 7) // 8):
                bits = 8  # to chop off excess bits on the right
                if byte * 8 > end - 8:
                    bits = end - byte * 8
                # if verbose: print "byte =", byte, "bits =", bits
                mask = 0xFF  # to chop off excess bits on the left
                if byte == start // 8:
                    mask = (1 << (8 - start % 8)) - 1
                # if verbose: print "mask = %02x" % mask
                val = (val << bits) + ((data[byte] & mask) >> (8 - bits))
                # if verbose: print "data[byte] = %02x val = %02x" % (ord(data[byte]), val)
            return val

        cardtypes = {0: "anonymous", 2: "personal"}

        cardid = getbits(data[0:4], 0, 4 * 8)
        cardtype = cardtypes[getbits(data[0x10:0x36], 18 * 8 + 4, 19 * 8)]
        validuntildays = getbits(data[0x10:0x36], 11 * 8 + 6, 13 * 8 + 4)
        validuntil = datetime.date(1997, 1, 1)
        validuntil += datetime.timedelta(validuntildays)

        logger.debug(f"RAW DATA: {data.hex()}")

        s = "OV-Chipkaart id %d, %s, valid until %s" % (cardid, cardtype, validuntil)
        logger.info(s)

        # return {'cardid': cardid, 'cardtype': cardtype, 'validuntil': str(validuntil)}
        return {"validuntil": str(validuntil)}

    def collect_ovchipkaart(self):
        # OV chipcards use Mifare Classic (SAK == 0x18), looks like we can check this on .clf.target.sen_sel
        if self.target.clf.target.sel_res != b"\x18":
            logger.debug(
                f"No OV Chipkaart, No Mifare classic 4k. SAK (.clf.target.sel_res ({self.target.clf.target.sel_res})) is not b'\x18'"
            )
            return {}

        # we use our own authenticate method (was not implemented in nfcpy)
        try:
            # OV-chipkaart uses all-zeroes keys for its first few blocks/pages/whatever they are called)
            self._authenticate()
        except Exception as e:
            logger.debug(e, exc_info=True)
            return {}

        # is OV Chip kaart, match page2 vs known string.
        # read(1)[0:11] match: bytearray.fromhex('840000000603a00013aee4')
        data = [None, None, None, None]

        data[1] = self._read(1)
        # data[1] = self.target.read(1)
        if data[1][0:11] != bytearray.fromhex("840000000603a00013aee4"):
            logger.debug("collect_ovchipkaart: Not an OV Chipkaart.")
            return {}

        # read other pages
        data[0] = self._read(0)
        data[2] = self._read(2)
        data[3] = self._read(3)

        # parse meta info
        meta = self.parse_ovchipkaart(data[0] + data[1] + data[2] + data[3])
        return {"ovchipkaart": meta}

    def collect_meta(self):
        meta = {}

        # add nfc.tag.Tag type, product, exact class (Type 1/2/3/4 etc..):
        meta.update(
            {
                "tag": {
                    "class": str(type(self.target)),
                    "type": self.target.type,
                    "product": self.target.product,
                }
            }
        )

        # add nfc.clf.RemoteTarget: sel_res, sens_res,  sdd_res and brty
        meta.update(
            {
                "target": {
                    "brty": self.target.clf.target.brty,
                    "sdd_res": self.target.clf.target.sdd_res.hex(),
                    "sel_res": self.target.clf.target.sel_res.hex(),
                    "sens_res": self.target.clf.target.sens_res.hex(),
                }
            }
        )

        # try OV chiptkaart:
        meta.update(self.collect_ovchipkaart())

        # return all meta info
        return meta
