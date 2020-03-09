# from .data_container import data_container as dc
from .base import hw12vOut
import time

class Solenoid(hw12vOut):
	config_name = 'solenoid'
	time_wait = 1.8
	
	def __init__(self):
		# read gpio_pin from config
		self.gpio_pin = self.config.get('pin')

		# amount of time the door is open
		self.time_wait = self.config.get('time', self.time_wait)
		
		# hw_init
		self.hw_init()


	def trigger(self):
		self.open()
		
	def open(self):
		'''open the door, turn Solenoid on for self.time seconds. '''
		self.logger.debug('{:s} open.'.format(self.log_name))

		#
		# set GPIO_PIN high for x amount of time
		#
		# GPIO.output(self.gpio_pin, GPIO.HIGH)
		# # if self.ui is not None:
		# 	# self.ui.ui_on_door_open()
		#
		time.sleep(self.time_wait)
		# GPIO.output(self.gpio_pin, GPIO.LOW)
		#
		# if self.ui is not None:
		# 	self.ui.ui_off_door_open()

		self.logger.debug('{:s} close.'.format(self.log_name))


	def my_callback(self, channel):
		'''callback function for event_detect, called when button is pressed.'''

		if GPIO.input(channel) == 0:
			# prevent acting on glitches in the GPIO or cabling, proceed if the input is still low
			self.logger.info('{:s} pressed .'.format(self.log_name))

			if self.solenoid is not None:
				self.solenoid.open()

		else:
			# for those who are curious we will log false positives in our debug log
			self.logger.debug('{:s} False positive detected (input High).'.format(self.log_name))

