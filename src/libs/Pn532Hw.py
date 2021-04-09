from .base import DoorlockdBaseClass, dc
from .Led import LedMethods
from .UiLeds import UiLeds_4leds




class Led(DoorlockdBaseClass, LedMethods):
	'''hardware: LED output GPIO control.'''
	
					
	def __init__(self, gpio_pin, config_name='led', hw_init=True, pn532_gpio=None, no_cache_cfg=True):
		if gpio_pin == 'dummy' or gpio_pin == 'aux1':
			# let's make this Led a dummy:
			self.on = self.dummy
			self.off = self.dummy 
			
		# no_cache_cfg: set False if you config multiple Led, use pn532_gpio.hw_write_cfg() to write cfg
		self.no_cache_cfg = no_cache_cfg
			

		if pn532_gpio is None:
			raise ValueError('argument pn532_gpio must be set to an instance of the pn532gpio class')

		self.gpio_pin = gpio_pin
		self.config_name = config_name
		self.pn532_gpio = pn532_gpio
		
		if (hw_init):
			self.hw_init()
		
	def hw_init(self):
		self.pn532_gpio.cfg_gpio_set(self.gpio_pin, 0x3, self.no_cache_cfg) # 0x3 : 'Push/pull output'
		self.logger.info('initializing {} on gpio pin PN532:{:s}.'.format(self.config_name, str(self.gpio_pin)))
		
		
	def on(self):
		self.pn532_gpio.gpio_on(self.gpio_pin)
		
	def off(self):
		self.pn532_gpio.gpio_off(self.gpio_pin)
		
	def dummy(self):
		pass	
		
class UiLeds_4leds_Pn532(UiLeds_4leds):
	config_name = '4leds_pn532'
	pn532gpio = None
	#	[ui_leds.4leds_pn532]
	# 	led1 = "p30"
	# 	led2 = "p31" # or "dummy" or "aux1"
	# 	led3 = "p32"
	# 	led4 = "p33"	
	
	def __init__(self, pn532_gpio=None):
		if pn532_gpio is None:
			raise ValueError('argument pn532_gpio must be set to an instance of the pn532gpio class')
		# set our pn532 GPIO controller:
		self.pn532_gpio = pn532_gpio
		
		
		self.hw_init()
		self.events_init()

	def hw_init(self):
		self.logger.info('initializing {}.'.format(self.config_name))
		# assign Leds ports (can be p3x/p7x or 'dummy' )
		self.l1 = Led(self.config.get('led1', "p30"), 'led1', pn532_gpio=self.pn532_gpio)
		self.l2 = Led(self.config.get('led2', "p31"), 'led2', pn532_gpio=self.pn532_gpio)
		self.l3 = Led(self.config.get('led3', "p32"), 'led3', pn532_gpio=self.pn532_gpio)
		self.l4 = Led(self.config.get('led4', "P33"), 'led4', pn532_gpio=self.pn532_gpio)
		
		# write cfg to hardware.
		self.pn532_gpio.hw_write_cfg()
		
		# configure aux1 port:  
		# ini config: aux = "0x[1-f]" 
		aux1 = self.config.get('aux1', None)
		if aux1 is not None:
			self.pn532_gpio.cfg_aux_set(aux1=int(aux1, 16))
		

class Pn532Button(DoorlockdBaseClass):
	'''hardware: Button input class.'''
	counter = 0
	
					
	def __init__(self, config_name='button', hw_init=True, pn532_gpio=None, no_cache_cfg=False, trigger_action='not set'):			
		# no_cache_cfg: set False if you config multiple Led, use pn532_gpio.hw_write_cfg() to write cfg
		self.no_cache_cfg = no_cache_cfg
			

		# read trigger_action from config or use the hardcoded default from the init argument.
		self.trigger_action = self.config.get('trigger_action', trigger_action)

		if pn532_gpio is None:
			raise ValueError('argument pn532_gpio must be set to an instance of the pn532gpio class')

		# read gpio_pin from config
		self.gpio_pin = self.config.get('pin', 'p72')
		
		self.config_name = config_name
		self.pn532_gpio = pn532_gpio
		
		if (hw_init):
			self.hw_init()
		
	def hw_init(self):
		self.pn532_gpio.cfg_gpio_set(self.gpio_pin, 0x2, self.no_cache_cfg) # 0x2 : 'input'
		self.logger.info('initializing {} on gpio pin PN532:{:s}.'.format(self.config_name, str(self.gpio_pin)))
		
		# set event detect
		self.pn532_gpio.add_event_detect(self.gpio_pin, False, self.trigger)
		
		
	@property
	def status(self):
		return self.pn532_gpio.gpio_get(self.gpio_pin)


	def trigger(self):		
		# raise button push event
		# dc.e.raise_event('{}_pushed'.format(self.config_name)) # raise button?_pushed when button is pushed
		dc.e.raise_event('button_pushed') # raise button?_pushed when button is pushed
		
		# raise configured trigger_action + _button_pushed event:
		# dc.e.raise_event("{}_button_pushed".format(self.trigger_action)) # raise configured trigger_action + button_pushed for this Button
		
		# raise configured trigger_action event:
		dc.e.raise_event(self.trigger_action) # raise configured trigger_action for this Button
		self.counter = self.counter + 1
				

	def hw_exit(self):
		'''exit/de-initialize gpio port.'''
		self.logger.info('exitting {} on gpio pin {:s}.'.format(self.config_name, str(self.gpio_pin)))
		#
		self.pn532_gpio.remove_event_detect(self.gpio_pin)
