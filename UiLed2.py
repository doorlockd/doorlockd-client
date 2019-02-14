#!/usr/bin/env python
#
import Adafruit_BBIO.GPIO as GPIO
import time


#
# example: ui_leds = UiLed2("P9_13", "P9_12")
#
class UiLed2:
    '''Dual Led user feedback interface.'''

    def __init__(self, gpio_pin_green, gpio_pin_red, logger=None):
        '''setup feedback LEDs'''

	# dress up logger object. use logger or dummy without configuring dummy before. 
	self.logger = logger or logging.getLogger('dummy') 

        self.logger.info('init {:s} on gpio green led: {:s}, red led: {:s}.'.format(self.__class__.__name__,gpio_pin_green, gpio_pin_red))

        self.gpio_pin_green = str(gpio_pin_green)
        self.gpio_pin_red = str(gpio_pin_red)

       	GPIO.setup(self.gpio_pin_green, GPIO.OUT)
       	GPIO.setup(self.gpio_pin_red, GPIO.OUT)


    def cleanup(self):
        '''cleanup individual GPIO pins: remove event detect and set to GPIO.IN with GPIO.PUD_OFF'''
	for gpio_pin in [ self.gpio_pin_green, self.gpio_pin_red ]:
        	self.logger.debug('cleanup ' + self.__class__.__name__+ ': cleanup single GPIO pin ' + gpio_pin)
		GPIO.remove_event_detect(gpio_pin)
        	GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    def green_status(self):
        '''status green LED'''
	print Adafruit_BBIO.GPIO.gpio_function(self.gpio_pin_green)
        self.logger.debug(self.__class__.__name__+ ':  green led status ')

    def green_on(self):
        '''Green LED on'''
	GPIO.output(self.gpio_pin_green, GPIO.HIGH)
        self.logger.debug(self.__class__.__name__+ ':  green led on ')

    def red_on(self):
        '''Red LED off'''
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
        self.logger.debug(self.__class__.__name__+ ':  red led on ')

    def green_off(self):
        '''Green LED off'''
	GPIO.output(self.gpio_pin_green, GPIO.LOW)
        self.logger.debug(self.__class__.__name__+ ':  green led off ')

    def red_off(self):
        '''Red LED off'''
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
        self.logger.debug(self.__class__.__name__+ ':  red led off ')

    def green_blink_once(self):
        '''Blink Green LED once'''
        #self.logger.debug(self.__class__.__name__+ ':  blink green led ')
	GPIO.output(self.gpio_pin_green, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(self.gpio_pin_green, GPIO.LOW)

    def red_blink_once(self):
        '''Blink Red LED once'''
        self.logger.debug(self.__class__.__name__+ ':  blink red led ')
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)


    def ui_pulse_comm(self):
        '''show RFID or Database communication.'''
	self.red_blink_once()

    def ui_on_door_open(self):
        '''turn Door is open indicator.'''
	self.green_on()

    def ui_off_door_open(self):
        '''turn off door open indicator.'''
	self.green_off()

    def ui_show_access_false(self):
        '''show access denied (will wait for 1.5 seconds).'''
	time.sleep(0.2)
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(1.5)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
	time.sleep(0.3)

    def ui_show_comm_error(self):
        '''show access denied (will wait for 1.5 seconds).'''
	time.sleep(0.2)
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(0.3)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
	time.sleep(0.2)
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(0.3)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
	time.sleep(0.4)



