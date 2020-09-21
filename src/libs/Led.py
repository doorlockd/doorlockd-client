from .base import hwLed
import time
import threading


# o	off
# * on
# . blink_once
# x signal -__--__-

class Led(hwLed):
	'''hardware: LED output GPIO control.'''
	
	def __init__(self, gpio_pin, config_name='led', hw_init=True):
		self.gpio_pin = gpio_pin
		self.config_name = config_name
		
		if (hw_init):
			self.hw_init()

	def blink(self):
		self.on()
		time.sleep(0.05)
		self.off()
	
	def signal(self):
		'''show signal for 2.x seconds.'''
		self.on()
		time.sleep(0.6)
		self.off()
		time.sleep(0.3)
		self.on()
		time.sleep(0.6)
		self.off()
		time.sleep(0.3)
		self.on()
		time.sleep(0.6)
		self.off()
		
		
	