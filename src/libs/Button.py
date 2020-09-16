from .base import hwButtonInput, GPIO, dc, baseTriggerAction
import time

class Button(hwButtonInput):
	config_name = 'not set'
	trigger_action = 'not set' # open_door|ring_buzzer|whatever
	
	counter = 0
	
	def __init__(self, config_name, trigger_action='not set'):
		self.config_name = config_name
		
		# read gpio_pin from config
		self.gpio_pin = self.config.get('pin')

		# read trigger_action from config or use the hardcoded default from the init argument.
		self.trigger_action = self.config.get('trigger_action', trigger_action)

		# hw_init
		self.hw_init()


	def trigger(self):		
		# raise trigger_action event:
		dc.e.raise_event(self.trigger_action)
		self.counter = self.counter + 1
				

		