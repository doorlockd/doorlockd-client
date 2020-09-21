from .base import DoorlockdBaseClass, dc
from .Led import Led
import time
import threading


# 4 leds
# o	off
# * on
# . blink
# x signal -__--__-

# 1 2 3 4 | LEDs
# * o o o ( hw ready )
# i . i i ( rfid comm pulse)
# i * i i ( rfid comm ready)
# i i x i ( rfid denied )
# i i * i ( rfid access )
# i i i * ( door open )
# i i i o ( door close )
# i i . i ( button1_pressed)
# i i i . ( button2_pressed)


class UiLeds(DoorlockdBaseClass):
	config_name = 'ui_leds'
	#	[ui_leds]
	# 	led1 = "P9_14"
	# 	led2 = "P9_16"
	# 	led3 = "P8_13"
	# 	led4 = "P8_19"	

	def __init__(self):
		self.l1 = Led(self.config.get('led1', "P9_14"), 'led1')	
		self.l2 = Led(self.config.get('led2', "P9_16"), 'led2')	
		self.l3 = Led(self.config.get('led3', "P8_13"), 'led3')	
		self.l4 = Led(self.config.get('led4', "P8_19"), 'led4')	

		# detach event call back (ecb) functions
		dc.e.subscrine('rfid_ready', self._ecb_rfid_ready)
		dc.e.subscrine('rfid_comm_pulse', self._ecb_rfid_comm_pulse)
		dc.e.subscrine('rfid_comm_ready', self._ecb_rfid_comm_ready)
		dc.e.subscrine('rfid_denied(', self._ecb_rfid_denied()
		dc.e.subscrine('rfid_access(', self._ecb_rfid_access()
		dc.e.subscrine('door_open(', self._ecb_door_open()
		
	def _ecb_rfid_ready(self):
		self.l1.on()
		self.l2.off()
		self.l3.off()
		self.l4.off()
	
	def _ecb_rfid_comm_pulse(self):
		self.l2.blink()

	def _ecb_rfid_comm_ready(self):
		self.l2.on()

	def _ecb_rfid_denied(self):
		self.l3.signal()
		## after signal is finished
		# self.l2.off()

	def _ecb_rfid_access(self):
		self.l2.on()
		self.l3.on()

	def _ecb_door_open(self):
		self.l4.on()

	def _ecb_door_close(self):
		self.l4.off()

	
	def selftest(self):
		for ln in ['l1', 'l2', 'l3', 'l4']:
			led = getattr(self, ln)
			print("LED selftest: {}, {}, {}".format(ln, led.config_name, led.gpio_pin))

		for action in ['blink_once','on', 'off', 'signal']:
			for ln in ['l1', 'l2', 'l3', 'l4']:
				led = getattr(self, ln)
				print("LED test: {}, {}()".format(ln, action))
				getattr(led, action)()	# call method action on led : led.action()
				time.sleep(0.25)
			time.sleep(1)
		print("LED selftest finished")

