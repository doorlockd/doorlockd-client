from .base import hwButtonInput, GPIO, dc
import time

class Button(hwButtonInput):
	config_name = 'not set'
	trigger_action = 'not set' # solenoid|buzzer|whatever
	
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
		# call trigger on destination hw
		if dc.hw.get(self.trigger_action, None) is not None:
			if dc.hw[ self.trigger_action ] is not self:
				dc.hw[ self.trigger_action ].trigger()
				self.counter = self.counter + 1
			else:
				self.logger.warn('Trigger error on {:s}: action is looping back to self !!!{:s}.'.format(self.config_name, self.trigger_action))
		else:
			self.logger.error('Trigger error on {:s}: action {:s} has no trigger() method.'.format(self.config_name, self.trigger_action))

		