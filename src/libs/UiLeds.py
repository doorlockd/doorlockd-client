from .base import DoorlockdBaseClass, hwLed, dc
import time
import threading


# 4 leds
# o	off
# * on
# . blink
# x signal -__--__-

# * o o o ( hw available )
# * . o o ( rfid comm )
# * * x o ( rfid denied )
# * * * o ( rfid access )
# * * * * ( door open )
# * o . o ( button1_pressed)
# * o o . ( button2_pressed)


class UiLeds(DoorlockdBaseClass):
	config_name = 'ui_leds'

	def __init__(self):
	#	[ui_leds]
	# 	led1 = "P9_14"
	# 	led2 = "P9_16"
	# 	led3 = "P8_13"
	# 	led4 = "P8_19"
	
		self.l1 = hwLed(self.config.get('led1', "P9_14"), 'led1')	
		self.l2 = hwLed(self.config.get('led2', "P9_16"), 'led2')	
		self.l3 = hwLed(self.config.get('led3', "P8_13"), 'led3')	
		self.l4 = hwLed(self.config.get('led4', "P8_19"), 'led4')	

	def selftest(self):
		for ln in ['l1', 'l2', 'l3', 'l4']:
			led = getattr(self, ln)
			print("LED selftest: {}, {}, {}".format(ln, led.config_name, led.gpio_pin))
			for action in ['on', 'off', 'blink_one']:
				print("LED test: {}, {}()".format(ln, action))
				getattr(led, action)()	# call method action on led : led.action()
				time.sleep(1)
		print("LED selftest finished")

