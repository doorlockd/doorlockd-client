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

	def blink(self, duration=0.05):
		self.on()
		time.sleep(duration)
		self.off()
	
	def short(self):
		self.blink(0.1)
		
	def medium(self):
		self.blink(0.3)
		
	def long(self):
		self.blink(0.6)
	
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


class DuoLed(hwLed):
	'''hardware: LED output GPIO control.'''
	
	def __init__(self, gpio_pin_red, gpio_pin_green, config_name='duoled', hw_init=True):
		self.gpio_pin_red = gpio_pin_red 
		self.gpio_pin_green = gpio_pin_green 
		self.config_name = config_name
		
		
		if (hw_init):
			self.hw_init()

	def on(self):
		# do both leds 
		self.y.on()
	
	def off(self):
		# do both leds
		self.y.off()
	


	def hw_init(self):
		# Red
		self.r = Led(self.gpio_pin_red, 'led_red')
		
		# Green
		self.g = Led(self.gpio_pin_green, 'led_green')
		
		# Yello
		self.y = DuoLedYellow(self.r, self.g)
		
	def hw_exit(self):
		self.r.hw_exit()
		self.g.hw_exit()
		self.y.hw_exit()
		
		
		

	class DuoLedYellow(Led):
		# implements Led function for yellow

		def __init__(self, led_red, led_green, config_name='led_yellow'):
			self.config_name = config_name
		
			self.red = led_red;
			self.green = led_green;

		def on(self):
			self.red.on()
			self.green.on()
		
		def onff(self):
			self.red.off()
			self.green.off()
		

		# disabled some methods:
		def hw_init(self):
			pass
		
		def hw_exit(self):
			pass