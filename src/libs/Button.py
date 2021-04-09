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
		# raise button push event
		# dc.e.raise_event('{}_pushed'.format(self.config_name)) # raise button?_pushed when button is pushed
		dc.e.raise_event('button_pushed') # raise button?_pushed when button is pushed

		# raise configured trigger_action + _button_pushed event:
		# dc.e.raise_event("button_pushed_{}".format(self.trigger_action)) # raise configured trigger_action + button_pushed for this Button
		
		# raise configured trigger_action event:
		dc.e.raise_event(self.trigger_action) # raise configured trigger_action for this Button
		self.counter = self.counter + 1
				

		