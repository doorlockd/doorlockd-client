
class IO:	
	INPUT = 0
	OUTPUT = 1



class IOPort(object):	

	pin = None
	has_input = False
	has_output = False
	
	def __init__(self, pin, direction=None, io_chip=None, limit_direction=None, *args, **kwargs):
		"""
		IO Port Object to control, read and write the input and output value.
		"""			
		self.pin = pin
		
		# set parent io_chip
		if io_chip:
			self.io_chip = io_chip

		if limit_direction is not None:
			self.limit_direction = limit_direction

		if direction is not None:
			self.setup(direction, *args, **kwargs)
		

	def setup(self, direction):
		"""setup as INPUT: 0 / OUTPUT: 1."""
		
		# check limit_direction
		if hasattr(self, 'limit_direction') and self.limit_direction is not direction:
			raise Exception("this IOPort can not become '{}', it is limited to '{}'".format(direction, self.limit_direction))

		# setup on io_chip
		self.io_chip.setup(self, direction)
		return(self)
		
	def cleanup(self):
		"""Cleanup one pin"""
		self.io_chip.cleanup(self.pin)
			
	def input(self):
		"""return True/False"""
		if self.has_input:
			return self.io_chip.input(self.pin)
		
		else:
			raise Exception("this IOPort is not configured as input")
		
		
	def output(self, value):
		"""set True/False"""
		if self.has_output:
			self.io_chip.output(self.pin, value)

		else:
			raise Exception("this IOPort is not configured as output")

	
	def add_event_detect(self, edge, callback, *xargs, **kwargs):
		self.io_chip.add_event_detect(self.pin, edge, callback, *xargs, **kwargs)

	def remove_event_detect(self, *xargs, **kwargs):
		self.io_chip.remove_event_detect(self.pin, *xargs, **kwargs)

	
class IOChip:
	__io_port_class = IOPort
	
	def __init__(self, *args, **kwargs):
		"""What ever is needed to init or connect your GPIO chip"""
		pass
	
	def input(self, pin):
		raise NotImplementedError()

	def output(self, pin, value):
		raise NotImplementedError()
	
	def setup(self, port, direction):
		raise NotImplementedError()
		
	def cleanup(self, pin=None):
		"""Cleanup one pin, or cleanup all pins for this IO Chip"""
		raise NotImplementedError()
	
	def Port(self, pin, direction=None, *args, **kwargs):
		return self.__io_port_class(pin, direction, io_chip=self, *args, **kwargs)
		
	def add_event_detect(self,pin, edge, callback, *xargs, **kwargs):
		raise NotImplementedError()
		
	def remove_event_detect(self,pin,  *xargs, **kwargs):
		raise NotImplementedError()
	