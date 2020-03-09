from .data_container import data_container as dc


class DoorlockdBaseClass():
	config_name = None
		
	#
	# configs
	#
	@property
	def config(self):
		return(dc.config.get(self.config_name,{}))
	
	
	#
	# logging 
	#
	@property
	def logger(self):
		return(dc.logger)

	@property
	def log_name(self):
		return('{:s}:{:s}'.format(self.__class__.__name__, str(self.config_name)))

	def log(self, level, message):
		self.logger.log(level,'{:s} :{:s}'.format(self.log_name, message))
	
	

class hw12vOut(DoorlockdBaseClass):
	'''hardware: 12Volt output GPIO control.'''
	
	__gpio_pin = None
	# config_name = 'hw_test'
	
	def __init__(self):
		pass
		# self.config_name = 'hw_test'
	
	@property
	def gpio_pin(self):
		return(self.__gpio_pin)
	
	@gpio_pin.setter
	def gpio_pin(self, gpio_pin):
		'''only set gpio if not initiated.'''
		self.__gpio_pin = str(gpio_pin) # make sure it's a string.	
	
	def hw_init(self):
		'''initialize gpio port.'''
		self.logger.info('initializing on gpio pin {:s}.'.format(str(self.gpio_pin)))

		# GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
		
	@property
	def log_name(self):
		return('{:s}:{:s}'.format(self.__class__.__name__, str(self.gpio_pin)))
	
	@property
	def status(self):
		return(False)
		return(bool(GPIO.input(self.gpio_pin)))

	@status.setter
	def status(self, state):
		if state is not self.status:
			self.trigger()
			
