import libs.IOWrapper as IO
from libs.data_container import data_container as dc

# logger = dc.logger


import nfc

# from nfc.clf import RemoteTarget

import libs.IOWrapper.PN532
from libs.pn532gpio import pn532Gpio


class TestPN532:

    def __init__(self, config={}):
        # initialize myself
        #
        # initilialize pn532
        self.clf = nfc.ContactlessFrontend("ttyS2:pn532")
        # use pn532 hardware
        io_pn532 = IO.PN532.IOChip(pn532Gpio(self.clf))

        # dc.io_port['p71'] = io_pn532.Port('p71')
        for k in config["io_export"].keys():
            dc.logger.info(
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

        # p30 = io_pn532.Port('p30').setup(IOWrapper.OUTPUT)
        # p31 = io_pn532.Port('p31').setup(IOWrapper.OUTPUT)
        # p71 = io_pn532.Port('p71').setup(IOWrapper.OUTPUT)
        # p72 = io_pn532.Port('p72').setup(IOWrapper.INPUT)

        # dc.io_port['p30'] = io_pn532.Port('p30')
        # dc.io_port['p31'] = io_pn532.Port('p31')
        # dc.io_port['p71'] = io_pn532.Port('p71')
        # dc.io_port['p72'] = io_pn532.Port('p72')

    def setup(self):
        # setup module
        pass

    def enable(self):
        # enable module
        pass

    def disable(self):
        # disable module
        pass

    def teardown(self):
        # de-setup module
        # remove pn532
        self.clf.close()
