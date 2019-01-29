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

	try:
        	GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		GPIO.add_event_detect(self.gpio_pin,GPIO.FALLING,callback=self.my_callback,bouncetime=200) 
	
	except:
        	logger.info('failed to setup {:s} using name {:s} on gpio pin {:s}.'.format(self.__class__.__name__, name, gpio_pin))
		raise SystemExit('Unable to setup button using GPIO pin: %s' % gpio_pin)

    def cleanup(self):
        '''cleanup single GPIO pin: remove event detect and set to GPIO.IN with GPIO.PUD_OFF'''

        logger.debug('cleanup ' + self.__class__.__name__+ ': cleanup single GPIO pin ' + self.gpio_pin)
	GPIO.remove_event_detect(self.gpio_pin)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)


    def my_callback(self, channel):
	logger.info('{:s} {:s} pressed .'.format(self.__class__.__name__, self.name))

	if GPIO.input(self.gpio_pin) == 1:
		# falss positive 
		logger.debug('{:s} {:s} False positive detected (input High).'.format(self.__class__.__name__, self.name))
	else:
		logger.debug('{:s} {:s} (input Low) .'.format(self.__class__.__name__, self.name))

		if self.solenoid is not None:
			self.solenoid.open()


