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

	def blink_once(self):
		self.on()
		time.sleep(0.05)
		self.off()
	
	def signal(self, wait=False):
		'''show signal for 2 seconds.'''
		time_wait = 2
		
		# set signal with pwm
		self.pwm(50, 1)
		
		# do we block ot wait in a new thread
		if wait:
			time.sleep(time_wait)
			self.off()
		else:
			t = threading.Timer(time_wait, self.off)
			t.start()  # after self.time_wait seconds, trigger_end() will be executed

