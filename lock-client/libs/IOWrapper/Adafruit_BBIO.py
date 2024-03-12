from . import interface
from .. import IOWrapper as IO

import Adafruit_BBIO.GPIO as GPIO
import threading

#
#  example IOChip and IOPort interface
#


class IOPort(interface.IOPort):
    pass


class IOChip(interface.IOChip):
    __io_port_class = (
        IOPort  # you need this line , so it will call the above IOPort class
    )

    def setup(self, port, direction):
        """setup as INPUT: 0/OUTPUT: 1"""

        if direction == IO.INPUT:
            # setup INPUT
            GPIO.setup(port.pin, GPIO.IN)

            # set identity:
            port.has_input = True
            port.has_output = False

        if direction == IO.OUTPUT:
            # setup OUTPUT
            GPIO.setup(port.pin, GPIO.OUT)

            # set identity:
            port.has_input = True
            port.has_output = True

    def input(self, port):
        # do whatever you do to get input value for 'pin':
        return GPIO.input(port.pin)

    def output(self, port, value):
        # do whatever you do to set output value for 'pin':
        GPIO.output(port.pin, value)

    def add_event_detect(self, port, edge, callback, *xargs, **kwargs):
        # events add :

        if edge == IO.EDGE_RISING:
            gpio_edge = GPIO.RISING
        if edge == IO.EDGE_FALLING:
            gpio_edge = GPIO.FALLING

        # Adafruit_BBIO.GPIO.add_event_detect(channel, edge[, callback=None, bouncetime=0])
        # Adafruit callback need an extra argument (channel/pin ), so i've placed my callback in an lambda function
        # GPIO.add_event_detect(pin, gpio_edge, lambda x: callback( *xargs, **kwargs))
        GPIO.add_event_detect(
            port.pin,
            gpio_edge,
            lambda x: threading.Thread(
                target=callback, args=xargs, kwargs=kwargs
            ).start(),
        )

    def remove_event_detect(self, port):
        # events remove
        # TODO; incase there is need for more specific callback removal (by edge / callback function) i will need to write an extra callback wrapper.
        GPIO.remove_event_detect(port.pin)

    def cleanup(self, port=None):
        if port.pin:
            # one specific pin
            GPIO.remove_event_detect(port.pin)

        if port is None:
            # cleanup chip:
            GPIO.cleanup()
