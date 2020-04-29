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
	default_status = False 
	invert_status = False
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
		if self.invert_status:
			return(not bool(GPIO.input(self.gpio_pin)))
		else:
			return(bool(GPIO.input(self.gpio_pin)))

	@status.setter
	def status(self, state):
		# call trigger if new status != default_status or != current status
		if state is not self.default_status:
			if state is not self.status:
				self.trigger()
			else:
				self.logger.info('notice: {:s}: status update ignored ( status is already {:s})'.format(self.log_name, str(state)))
		else:
			self.logger.info('notice: {:s}: status update ignored ( just wait for status to change to default {:s})'.format(self.log_name, str(self.default_status)))
				
	def hw_exit(self):
		'''exit/de-initialize gpio port.'''
		self.logger.info('exitting {} on gpio pin {:s}.'.format(self.config_name, str(self.gpio_pin)))
		
		# remove event detect if any..
		GPIO.remove_event_detect(self.gpio_pin)
		# reset state by setting to GPIO.IN  and GPIO.LOW
		GPIO.setup(self.gpio_pin, GPIO.IN, initial=GPIO.LOW)
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.hw_exit()
				
	def __del__(self):
		self.hw_exit()
		


class hw12vOut(baseHardwareIO):
	'''hardware: 12Volt output GPIO control.'''
	default_status = False
	
	
	def hw_init(self):
		'''initialize gpio port.'''
		self.logger.info('initializing {} on gpio pin {:s}.'.format(self.config_name, str(self.gpio_pin)))

		try:
			GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
	
		except Exception as e:
			self.logger.info('failed to setup {:s} on {:s}.'.format(self.config_name, self.log_name))
			self.logger.info('Error: {:s}.'.format(str(e)))
			raise SystemExit('Unable to setup {:s} on {:s}'.format(self.config_name, self.log_name))
		
		
		

class hwButtonInput(baseHardwareIO):
	'''hardware: input button between GPIO and GND.'''
	default_status = False
	invert_status = True
	
	def hw_init(self):
		'''initialize gpio port.'''
		self.logger.info('initializing {} on gpio pin {:s}.'.format(self.config_name, str(self.gpio_pin)))

		try:
			GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.add_event_detect(self.gpio_pin,GPIO.FALLING,callback=self.__event_callback,bouncetime=200) 
	
		except Exception as e:
			self.logger.info('failed to setup {:s} on {:s}.'.format(self.config_name, self.log_name))
			self.logger.info('Error: {:s}.'.format(str(e)))
			raise SystemExit('Unable to setup {:s} on {:s}'.format(self.config_name, self.log_name))
		
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


			
class baseTriggerAction(DoorlockdBaseClass):
	'''base interface for object who function as 'trigger_action' on Button objects. 
	This class must implement an trigger() method.''' 	
	
	def trigger(self):
		raise NotImplementedError('trigger() method is missing.')
		
