from . import interface 
from .. import IOWrapper as IO
#
#  pn532Gpio IOChip and IOPort interface
#

class IOPort(interface.IOPort):
	pass
	
	
class IOChip(interface.IOChip):
	__io_port_class = IOPort # you need this line , so it will call the above IOPort class
	
	def __init__(self, pn532Gpio):
		self.pn532Gpio = pn532Gpio


	def setup(self, port,  direction):
		"""setup as INPUT: 0/OUTPUT: 1"""

		if direction == IO.INPUT:
			# setup INPUT
			self.pn532Gpio.cfg_gpio_set(port.pin, self.pn532Gpio.INPUT)
			
			# set identity:
			port.has_input = True
			port.has_output = False
	
		if direction == IO.OUTPUT:
			# setup OUTPUT
			self.pn532Gpio.cfg_gpio_set(port.pin, self.pn532Gpio.OUTPUT)
			
			# set identity:
			port.has_input = True
			port.has_output = True
			
		
		
	def input(self, port):
		# do whatever you do to get input value for 'pin':
		return self.pn532Gpio.gpio_get(port.pin)
		

	def output(self, port, value):
		# do whatever you do to set output value for 'pin':
		# print("DEBUG: pn532 gpio set (port, value)", (port.pin, value))
		self.pn532Gpio.gpio_set(port.pin, value)

	def add_event_detect(self, port, edge, callback):
		# events add
		self.pn532Gpio.add_event_detect(port.pin, edge, callback)
		
	def remove_event_detect(self,port, edge=None, callback=None):
		# events remove
		self.pn532Gpio.remove_event_detect(port.pin, edge, callback)

		
	def cleanup(self, port=None):
		if port.pin:
			# one specific pin
			self.pn532Gpio.remove_event_detect(port.pin)
		
		if port is None:
			# all pins:
			self.pn532Gpio.hw_exit()
			
	
