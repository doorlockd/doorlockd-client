# from .data_container import data_container as dc
from .base import hw12vOut, GPIO
import time
import threading

class Solenoid(hw12vOut, threading.Thread):
	config_name = 'solenoid'
	time_wait = 1.8
	counter = 0
	
	def __init__(self):
		# turn myself into a thread
		threading.Thread.__init__(self)
		
		# read gpio_pin from config
		self.gpio_pin = self.config.get('pin')

		# amount of time the door is open
		self.time_wait = self.config.get('time', self.time_wait)
		
		# hw_init
		self.hw_init()

		

	def trigger(self):
		'''open the door, turn Solenoid on for self.time seconds in background'''
		# self.deamon = True
		# run is called by threading.start  
		self.start()

	def run(self):
		'''open the door, turn Solenoid on for self.time seconds. '''
		self.logger.debug('{:s} open.'.format(self.log_name))

		#
		# set GPIO_PIN high for x amount of time
		#
		GPIO.output(self.gpio_pin, GPIO.HIGH)
		# # if self.ui is not None:
		# 	# self.ui.ui_on_door_open()
		#
		time.sleep(self.time_wait)
		GPIO.output(self.gpio_pin, GPIO.LOW)
		#
		# if self.ui is not None:
		# 	self.ui.ui_off_door_open()

		self.counter = self.counter + 1

		self.logger.debug('{:s} close.'.format(self.log_name))



