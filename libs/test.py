#!/usr/bin/env python3

import nfc

# from nfc.clf import RemoteTarget
import logging


import IOWrapper.PN532
import IOWrapper.Adafruit_BBIO

from pn532gpio import pn532Gpio

# use beagleboard hardware
io_bbio = IOWrapper.Adafruit_BBIO.IOChip()
p9_12 = io_bbio.Port("P9_12").setup(IOWrapper.OUTPUT)
p8_17 = io_bbio.Port("P8_17").setup(IOWrapper.INPUT)


p8_17.add_event_detect(
    IOWrapper.EDGE_RISING, lambda pin: p30.io_chip.pn532Gpio.gpio_invert(p30.pin)
)

#
# initilialize pn532
clf = nfc.ContactlessFrontend("ttyS2:pn532")
# use pn532 hardware
io_pn532 = IOWrapper.PN532.IOChip(pn532Gpio(clf))


p30 = io_pn532.Port("p30").setup(IOWrapper.OUTPUT)
p31 = io_pn532.Port("p31").setup(IOWrapper.OUTPUT)
p71 = io_pn532.Port("p71").setup(IOWrapper.OUTPUT)
p72 = io_pn532.Port("p72").setup(IOWrapper.INPUT)


p72.add_event_detect(IOWrapper.EDGE_RISING, lambda: p9_12.output(0))
p72.add_event_detect(
    IOWrapper.EDGE_FALLING,
    lambda: p9_12.output(1) or p31.io_chip.pn532Gpio.gpio_invert(p31.pin),
)


#
#
#
