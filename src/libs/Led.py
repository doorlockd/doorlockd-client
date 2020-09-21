from .base import hwLed
import time

class hwLed(baseHardwareIO):
	'''hardware: LED output GPIO control.'''
	
	def __init__(self, gpio_pin, config_name='led', hw_init=True):
		self.gpio_pin = gpio_pin
		self.config_name = config_name
		
		if (hw_init):
			self.hw_init()

	def blink_one(self):
		self.on()
		time.sleep(0.05)
		self.off()
	