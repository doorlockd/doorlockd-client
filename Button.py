#!/usr/bin/env python
#
import Adafruit_BBIO.GPIO as GPIO
import time

#
# setup logging
#
import logging
logger = logging.getLogger('doorlockd')


#
# example: button = Button("P8_12")
#
class Button:
    '''use an physical button connected to an GPIO and GND.'''

    def __init__(self, gpio_pin, name = 'button', solenoid=None ):
        '''setup an button and a callback function for opening a solenoid'''
        logger.info('init {:s} using name {:s} on gpio pin {:s}.'.format(self.__class__.__name__, name, gpio_pin))

        self.time = 1.8
        self.name = name # used in logfile
        self.gpio_pin = str(gpio_pin)
        self.solenoid = solenoid

        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	GPIO.add_event_detect(self.gpio_pin,GPIO.FALLING,callback=self.my_callback,bouncetime=200) # Setup event on pin switch_pin rising edge

    def cleanup(self):
        '''cleanup GPIO pins'''
        logger.debug('cleanup ' + self.__class__.__name__+ ': calling GPIO.cleanup() ')
	GPIO.cleanup() # Clean up

    def my_callback(self, channel):
	logger.info('{:s} {:s} pressed .'.format(self.__class__.__name__, self.name))
	if self.solenoid is not None:
		self.solenoid.open()
