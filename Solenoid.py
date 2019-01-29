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
# example: somedoor = Solenoid("P9_14")
#
class Solenoid:
    '''Control a Solenoid / Door unlocker.'''
    
    def __init__(self, gpio_pin, name = 'door'):
        ''' Initiate Solenoid object: setup GPIO.OUT pin and make sure the output is LOW (== door closed).'''
        logger.info('init {:s} using name {:s} on gpio pin {:s}.'.format(self.__class__.__name__, name, gpio_pin))

        self.time = 1.8
        self.name = name # used in logfile
        self.gpio_pin = str(gpio_pin)
        GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)

    def open(self):
        '''open the door, turn Solenoid on for self.time seconds. '''
        logger.debug('{:s} {:s} open .'.format(self.__class__.__name__, self.name))
        
        #
        # set GPIO_PIN high for x amount of time
        #
        GPIO.output(self.gpio_pin, GPIO.HIGH)
        time.sleep(self.time)
        GPIO.output(self.gpio_pin, GPIO.LOW)

        logger.debug('{:s} {:s} close .'.format(self.__class__.__name__, self.name))

        
    def cleanup(self):
        '''cleanup single GPIO pin: remove event detect and set to GPIO.IN with GPIO.PUD_OFF'''

        logger.debug('cleanup ' + self.__class__.__name__+ ': cleanup single GPIO pin ' + self.gpio_pin)
	GPIO.remove_event_detect(self.gpio_pin)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

