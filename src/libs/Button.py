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
			dc.hw[ self.trigger_action ].trigger()
			self.counter = self.counter + 1
		else:
			self.logger.error('Trigger action {:s} not for button {:s}.'.format(self.trigger_action, self.config_name))
			
	# invert the status for the input connected to GND
	@property
	def status(self):
		print("DEBUG: bool(GPIO.input(self.gpio_pin)) :", bool(GPIO.input(self.gpio_pin)) )
		return(not bool(GPIO.input(self.gpio_pin)))

	@status.setter
	def status(self, state):
		if state is not self.status:
			self.trigger()
	
		