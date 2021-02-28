from .base import DoorlockdBaseClass, dc
from .Led import LedMethods
from .UiLeds import UiLeds_4leds




class Led(DoorlockdBaseClass, LedMethods):
	'''hardware: LED output GPIO control.'''
	
					
	def __init__(self, gpio_pin, config_name='led', hw_init=True, pn532_gpio=None):
		if gpio_pin == 'dummy' or gpio_pin == 'aux1':
			# let's make this Led a dummy:
			self.on = lambda self: pass
			self.off = lambda self: pass 
			

		if pn532_gpio is None:
			raise ValueError('argument pn532_gpio must be set to an instance of the pn532gpio class')

		self.gpio_pin = gpio_pin
		self.config_name = config_name
		self.pn532_gpio = pn532_gpio
		
		if (hw_init):
			self.hw_init()
		
	def hw_init(self):
		self.logger.info('initializing {} on gpio pin PN532:{:s}.'.format(self.config_name, str(self.gpio_pin)))
		
		
	def on(self):
		self.pn532_gpio.gpio_on(self.gpio_pin)
		
	def off(self):
		self.pn532_gpio.gpio_off(self.gpio_pin)
		
		
		
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
		
		# configure aux1 port:  
		# ini config: aux = "0x[1-f]" 
		aux1 = self.config.get('aux1', None)
		if aux1 is not None:
			self.pn532gpio.cfg_aux_set(aux1=int(aux1, 16))
		
	
