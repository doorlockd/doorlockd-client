from .base import DoorlockdBaseClass, dc
from .Led import Led
import time
import threading




class UiLedsWrapper(DoorlockdBaseClass):
	'''Wrapper Class, will return the configured or requested UiLeds_'leds_type' object.'''
		
	def __new__(cls, leds_type=None):
		
		if (leds_type is not None):
			# overwrite leds_type
			leds_type = leds_type
		else:
			# get config value or set hardcoded default
			leds_type = dc.config.get('ui_leds',{}).get('leds_type', '4leds') # [none|4leds|duoled|...]
	
	
		# init leds_type:
		if(leds_type == '4leds'):
			return UiLeds_4leds()
		elif(leds_type == 'duoled'):
			return UiLeds_duoled()
		elif(leds_type == 'none'):
			return UiLeds_none()
		else:
			dc.logger.warning("Warning: UiLeds: leds_type = '{}' is unkown, using type 'none'".format(leds_type))
			return UiLeds_none()
			
			

		

class UiLeds_none(DoorlockdBaseClass):
	'''dummy UiLeds class, in case no Leds are configured.'''
	config_name = 'ui_leds.none'
	
	def __init__(self):
		self.hw_init()

	def hw_init(self):
		self.logger.info('initializing {}.'.format(self.config_name))
	
	# implement the only needed method
	def hw_exit(self):
		self.logger.info('exitting {}.'.format(self.config_name))
		
		pass
	
class UiLeds_4leds(DoorlockdBaseClass):
	config_name = 'ui_leds.4leds'
	#	[ui_leds.4leds]
	# 	led1 = "P9_14"
	# 	led2 = "P9_16"
	# 	led3 = "P8_13"
	# 	led4 = "P8_19"	

	def __init__(self):
		self.hw_init()
		self.events_init()
		
		
	def events_init(self):
		# attach event call back (ecb) functions
		
		# 4 leds
		# o	off
		# * on
		# . blink
		# x signal -__--__-

		# 1 2 3 4 | LEDs
		# o o o o ( rfid_stopped)
		# * o o o ( hw ready )
		# i . i i ( rfid comm pulse)
		# i * i i ( rfid comm ready)
		# i i x i ( rfid denied )
		# i i * i ( rfid access )
		# i i i * ( solenoid_open )
		# i i i o ( solenoid_close )
		# i i . i ( button1_pressed)
		# i i i . ( button2_pressed)
		
		dc.e.subscribe('rfid_ready', self._ecb_rfid_ready)
		dc.e.subscribe('rfid_stopped', self._ecb_rfid_stopped)
		dc.e.subscribe('rfid_comm_pulse', self._ecb_rfid_comm_pulse)
		dc.e.subscribe('rfid_comm_ready', self._ecb_rfid_comm_ready)
		dc.e.subscribe('rfid_access_denied', self._ecb_rfid_denied)
		dc.e.subscribe('rfid_access_allowed', self._ecb_rfid_access)
		dc.e.subscribe('solenoid_open', self._ecb_solenoid_open)
		dc.e.subscribe('solenoid_close', self._ecb_solenoid_close)
		dc.e.subscribe('button1_pushed', self._ecb_button1_pushed)
		dc.e.subscribe('button2_pushed', self._ecb_button2_pushed)
		
	def hw_init(self):
		self.logger.info('initializing {}.'.format(self.config_name))
		self.l1 = Led(self.config.get('led1', "P9_14"), 'led1')	
		self.l2 = Led(self.config.get('led2', "P9_16"), 'led2')	
		self.l3 = Led(self.config.get('led3', "P8_13"), 'led3')	
		self.l4 = Led(self.config.get('led4', "P8_19"), 'led4')	

		
	def hw_exit(self):
		self.logger.info('exitting {}.'.format(self.config_name))
		self.l1.hw_exit()
		self.l2.hw_exit()
		self.l3.hw_exit()
		self.l4.hw_exit()
		
	def _ecb_rfid_ready(self, data):
		self.l1.on()
		self.l2.off()
		self.l3.off()
		self.l4.off()
	
	def _ecb_rfid_stopped(self, data):
		self.l1.off()
		self.l2.off()
		self.l3.off()
		self.l4.off()
		
	
	def _ecb_rfid_comm_pulse(self, data):
		self.l2.blink()

	def _ecb_rfid_comm_ready(self, date):
		self.l2.on()

	def _ecb_rfid_denied(self, date):
		self.l3.signal()
		## after signal is finished
		# self.l2.off()

	def _ecb_rfid_access(self, date):
		self.l2.on()
		self.l3.on()

	def _ecb_solenoid_open(self, date):
		self.l4.on()

	def _ecb_solenoid_close(self, date):
		self.l4.off()

	def _ecb_button1_pushed(self, date):
		self.l3.blink()

	def _ecb_button2_pushed(self, date):
		self.l3.blink()


	
	def selftest(self):
		for ln in ['l1', 'l2', 'l3', 'l4']:
			led = getattr(self, ln)
			print("LED selftest: {}, {}, {}".format(ln, led.config_name, led.gpio_pin))

		for action in ['blink','on', 'off', 'signal']:
			for ln in ['l1', 'l2', 'l3', 'l4']:
				led = getattr(self, ln)
				print("LED test: {}, {}()".format(ln, action))
				getattr(led, action)()	# call method action on led : led.action()
				time.sleep(0.25)
			time.sleep(1)
		print("LED selftest finished")



class UiLeds_duoled(DoorlockdBaseClass):
	config_name = 'ui_leds.duoled'
	#	[ui_leds.4leds]
	# 	led_red = "P8_13"
	# 	led_green = "P8_19"	

	def __init__(self):
		self.hw_init()
		self.events_init()
		
		
	def events_init(self):
		# attach event call back (ecb) functions
		dc.e.subscribe('rfid_ready', self._ecb_rfid_ready)
		dc.e.subscribe('rfid_stopped', self._ecb_rfid_stopped)
		dc.e.subscribe('rfid_comm_pulse', self._ecb_rfid_comm_pulse)
		dc.e.subscribe('rfid_comm_ready', self._ecb_rfid_comm_ready)
		dc.e.subscribe('rfid_access_denied', self._ecb_rfid_denied)
		dc.e.subscribe('rfid_access_allowed', self._ecb_rfid_access)
		dc.e.subscribe('solenoid_open', self._ecb_solenoid_open)
		dc.e.subscribe('solenoid_close', self._ecb_solenoid_close)
		dc.e.subscribe('button1_pushed', self._ecb_button1_pushed)
		dc.e.subscribe('button2_pushed', self._ecb_button2_pushed)
		
		# 4 leds
		# o	off
		# * on
		# . blink (realy short pulse)
		# , short blink 
		# - medium long  blink
		# = long  blink
		# x signal - -- -

		# r g  | LED (Red , Green)
		# , o  ( rfid_stopped)
		# - -  ( rfid ready )
		# . .  ( rfid comm pulse)
		# i .  ( rfid comm ready)
		# x i  ( rfid denied )
		# * *  ( rfid access ) --> turn yellow
		# 0 *  ( solenoid_open ) --> turn green
		# 0 0  ( solenoid_close )
		# . .  ( button1_pressed)
		# . .  ( button2_pressed)
		
	def hw_init(self):
		self.logger.info('initializing {}.'.format(self.config_name))
		self.lr = Led(self.config.get('led_red', "P8_13"), 'led_red')	
		self.lg = Led(self.config.get('led_green', "P8_19"), 'led_green')	

		
	def hw_exit(self):
		self.logger.info('exitting {}.'.format(self.config_name))
		self.lr.hw_exit()
		self.lg.hw_exit()
		
	def _ecb_rfid_ready(self, data):
		self.lr.medium()
		self.lg.medium()
	
	def _ecb_rfid_stopped(self, data):
		self.lg.off() # and off
		self.lr.short() # and off
		
	
	def _ecb_rfid_comm_pulse(self, data):
		self.lr.blink()
		self.lg.blink()

	def _ecb_rfid_comm_ready(self, date):
		self.lg.blink()

	def _ecb_rfid_denied(self, date):
		self.lr.signal()
		## after signal is finished
		# self.lr.off()

	def _ecb_rfid_access(self, date):
		self.lr.on()
		self.lg.on()

	def _ecb_solenoid_open(self, date):
		self.lr.off()
		self.lg.on()

	def _ecb_solenoid_close(self, date):
		self.lr.off()
		self.lg.off()

	def _ecb_button1_pushed(self, date):
		self.lr.blink()
		self.lg.blink()

	def _ecb_button2_pushed(self, date):
		self.lr.blink()
		self.lg.blink()


	
	def selftest(self):
		for ln in ['l1', 'l2', 'l3', 'l4']:
			led = getattr(self, ln)
			print("LED selftest: {}, {}, {}".format(ln, led.config_name, led.gpio_pin))

		for action in ['blink','on', 'off', 'signal']:
			for ln in ['l1', 'l2', 'l3', 'l4']:
				led = getattr(self, ln)
				print("LED test: {}, {}()".format(ln, action))
				getattr(led, action)()	# call method action on led : led.action()
				time.sleep(0.25)
			time.sleep(1)
		print("LED selftest finished")
