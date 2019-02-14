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

    def green_on(self):
        '''Green LED on'''
	GPIO.output(self.gpio_pin_green, GPIO.HIGH)

    def red_on(self):
        '''Red LED off'''
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)

    def green_off(self):
        '''Green LED off'''
	GPIO.output(self.gpio_pin_green, GPIO.LOW)

    def red_off(self):
        '''Red LED off'''
	GPIO.output(self.gpio_pin_red, GPIO.LOW)

    def green_blink_once(self):
        '''Blink Green LED once'''
	GPIO.output(self.gpio_pin_green, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(self.gpio_pin_green, GPIO.LOW)

    def red_blink_once(self):
        '''Blink Red LED once'''
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)


    def ui_pulse_comm(self):
        '''show RFID or Database communication.'''
	self.logger.debug(self.__class__.__name__+ ': UI pulse communication')
	self.red_blink_once()

    def ui_on_door_open(self):
        '''turn Door is open indicator.'''
	self.logger.debug(self.__class__.__name__+ ': UI Door open ON')
	self.green_on()

    def ui_off_door_open(self):
        '''turn off door open indicator.'''
	self.logger.debug(self.__class__.__name__+ ': UI Door open OFF')
	self.green_off()

    def ui_show_access_false(self):
        '''show access denied (will wait for 1.5 seconds).'''
	self.logger.debug(self.__class__.__name__+ ': UI Access Denied')
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	self.green_blink_once()
	time.sleep(1.8)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
	time.sleep(0.3)

    def ui_show_comm_error(self):
        '''show access denied (will wait for 2.4 seconds).'''
	self.logger.debug(self.__class__.__name__+ ': UI communication error.')
	time.sleep(0.2)
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(0.3)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
	time.sleep(0.2)
	GPIO.output(self.gpio_pin_red, GPIO.HIGH)
	time.sleep(0.3)
	GPIO.output(self.gpio_pin_red, GPIO.LOW)
	time.sleep(0.4)



