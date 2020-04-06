from .data_container import data_container as dc
import Adafruit_BBIO.GPIO as GPIO


class DoorlockdBaseClass():
	config_name = None
		
	#
	# configs
	#
	@property
	def config(self):
		'''returns conig dict. Use self.cofig.get('key name' [, 'default value']) '''
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

		GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
		
	@property
	def log_name(self):
		return('{:s}:{:s}'.format(self.__class__.__name__, str(self.gpio_pin)))
	
	# status can be exposed to api
	@property
	def status(self):
		# return(False)
		return(bool(GPIO.input(self.gpio_pin)))

	@status.setter
	def status(self, state):
		if state is not self.status:
			self.trigger()
			

class hwButtonInput(DoorlockdBaseClass):
	'''hardware: input button between GPIO and GND.'''
	
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

		try:
			GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.add_event_detect(self.gpio_pin,GPIO.FALLING,callback=self.__event_callback,bouncetime=200) 
	
		# except Exception as e:
		# 	self.logger.info('failed to setup {:s} using name {:s} on gpio pin {:s}.'.format(self.__class__.__name__, self.config_name, self.gpio_pin))
		# 	self.logger.info('error: {:s}.'.format(str(e)))
		# 	raise SystemExit('Unable to setup button using GPIO pin: %s' % gpio_pin)
		
	def __event_callback(self, channel):
		'''callback function for event_detect, called when button is pressed.'''

		if GPIO.input(channel) == 0:
			# prevent acting on glitches in the GPIO or cabling, proceed if the input is still low
			self.logger.info('{:s} {:s} pressed .'.format(self.__class__.__name__, self.gpio_pin))

			# do the action:
			self.trigger()

		else:
			# for those who are curious we will log false positives in our debug log
			self.logger.debug('{:s} {:s} False positive detected (input High).'.format(self.__class__.__name__, self.gpio_pin))

		
	@property
	def log_name(self):
		return('{:s}:{:s}'.format(self.__class__.__name__, str(self.gpio_pin)))
	
	# status can be exposed to api
	@property
	def status(self):
		# return(False)
		return(bool(GPIO.input(self.gpio_pin)))

	@status.setter
	def status(self, state):
		if state is not self.status:
			self.trigger()
			
