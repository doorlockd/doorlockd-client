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
	
	
class baseHardwareIO(DoorlockdBaseClass):
	'''Base class for all gpio i/o hardware objects'''
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
	


class hw12vOut(baseHardwareIO):
	'''hardware: 12Volt output GPIO control.'''
	
	
	def hw_init(self):
		'''initialize gpio port.'''
		self.logger.info('initializing {} on gpio pin {:s}.'.format(self.config_name, str(self.gpio_pin)))

		GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
	
		

class hwButtonInput(baseHardwareIO):
	'''hardware: input button between GPIO and GND.'''

	def hw_init(self):
		'''initialize gpio port.'''
		self.logger.info('initializing {} on gpio pin {:s}.'.format(self.config_name, str(self.gpio_pin)))

		# try:
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
			self.logger.info('event: {:s} pressed .'.format(self.log_name))

			# do the action:
			self.trigger()

		else:
			# for those who are curious we will log false positives in our debug log
			self.logger.debug('input {:s} False positive detected (input High).'.format(self.log_name))

		# status can be exposed to api
		# invert the status for the input connected to GND
		@property
		def status(self):
			# return(False)
			return(not bool(GPIO.input(self.gpio_pin)))

		
			
