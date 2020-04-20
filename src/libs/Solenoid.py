# from .data_container import data_container as dc
from .base import hw12vOut, GPIO, baseTriggerAction
import time
import threading

class Solenoid(hw12vOut, baseTriggerAction):
	config_name = 'solenoid'
	time_wait = 1.8
	counter = 0
	
	def __init__(self):
		# read gpio_pin from config
		self.gpio_pin = self.config.get('pin')

		# amount of time the door is open
		self.time_wait = self.config.get('time', self.time_wait)
		
		# hw_init
		self.hw_init()

		
	def trigger(self):
		'''open the door, turn Solenoid on for self.time seconds. '''
		self.trigger_begin()

		# do the waiting
		t = threading.Timer(self.time_wait, self.trigger_end)
		t.start()  # after self.time_wait seconds, trigger_end() will be executed

		# self.trigger_end()

	def trigger_begin(self):
		'''open the door, turn Solenoid on for start'''
		# self.deamon = True
		self.logger.debug('{:s} open.'.format(self.log_name))
		self.counter = self.counter + 1

		#
		# set GPIO_PIN high for x amount of time
		#
		GPIO.output(self.gpio_pin, GPIO.HIGH)



	def trigger_end(self):
		'''open the door, turn Solenoid on for end. '''
		# # if self.ui is not None:
		# 	# self.ui.ui_on_door_open()
		#
		# time.sleep(self.time_wait)
		GPIO.output(self.gpio_pin, GPIO.LOW)
		#
		# if self.ui is not None:
		# 	self.ui.ui_off_door_open()


		self.logger.debug('{:s} close.'.format(self.log_name))



