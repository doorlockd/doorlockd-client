from .data_container import data_container as dc
from .base import hw12vOut, GPIO
import time

class Button(hwButtonInput):
	config_name = 'not set'
	trigger_action = 'not set' # solenoid|buzzer|whatever
	
	def __init__(self, config_name, trigger_action='not set'):
		# read gpio_pin from config
		self.gpio_pin = self.config.get('pin')

		# read trigger_action from config or use the hardcoded default from the init argument.
		self.trigger_action = self.config.get('trigger_action', trigger_action)

		# hw_init
		self.hw_init()


	def trigger(self):
		# call trigger on destination hw
		if dc.hw.get(self.trigger_action, None) is not None:
			dc.hw[ self.trigger_action ].trigger()
		else:
			self.logger.error('Trigger action {:s} not for button {:s}.'.format(self.trigger_action, self.config_name))
			
		