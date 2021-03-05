# from .data_container import data_container as dc
from .base import hw12vOut, GPIO, baseTriggerAction, dc
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
		self.time_wait = self.config.get('time_wait', self.time_wait)
		
		# hw_init
		self.hw_init()
		
		# subscribe to event 
		event_name = self.config.get('action_on', 'open_door') 
		dc.e.subscribe(event_name, self.event_callback)
		

	def event_callback(self, data):
		self.trigger(data.get('wait', False))
		
		
	def trigger(self, wait=False):
		'''open the door, turn Solenoid on for self.time seconds. '''
		self.trigger_begin()

		# do we block or wait in a new thread
		if wait:
			time.sleep(self.time_wait)
			self.trigger_end()
		else:
			t = threading.Timer(self.time_wait, self.trigger_end)
			t.start()  # after self.time_wait seconds, trigger_end() will be executed

	def trigger_begin(self):
		'''open the door, turn Solenoid on for start'''

		# set GPIO_PIN high for x amount of time
		#
		GPIO.output(self.gpio_pin, GPIO.HIGH)
		self.counter = self.counter + 1
		
		dc.e.raise_event('solenoid_open') # when solenoid is on
		self.logger.debug('{:s} open.'.format(self.log_name))



	def trigger_end(self):
		'''open the door, turn Solenoid on for end. '''

		GPIO.output(self.gpio_pin, GPIO.LOW)
		dc.e.raise_event('solenoid_close') # when solenoid is off
		self.logger.debug('{:s} close.'.format(self.log_name))



