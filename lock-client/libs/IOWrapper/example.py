import IOWrapper.interface as interface

#
#  example IOChip and IOPort interface
#

class IO:	
	INPUT = 0
	OUTPUT = 1


class IOPort(interface.IOPort):			
	pass

class IOChip(interface.IOChip):
	__io_port_class = IOPort # you need this line , so it will call the above IOPort class
	example_cntrl = None

	def setup(self, port,  direction):
		"""setup as INPUT: 0/OUTPUT: 1"""

		if direction == IO.INPUT:
			# setup INPUT
			# self.example_cntrl.setup(port.pin, INPUT)
			print(">>> setup pin:{} as INPUT".format(port.pin))
			
			# set identity:
			port.has_input = True
			port.has_output = False
	
		if direction == IO.OUTPUT:
			# setup OUTPUT
			# 
			# self.io_chip.example_cntrl.setup(port.pin, OUTPUT)
			print(">>> setup pin:{} as OUTPUT".format(port.pin))
			
			# set identity:
			port.has_input = True
			port.has_output = True
			
		
	def __init__(self, cntrl):
		# setup routine for this chip.
		EXAMPLE_CHIP.setup_example_chip(cntrl)
			
		
	def input(self, port):
		# do whatever you do to get input value for 'pin':
		print(">>> get input value for pin {}::{}".format(repr(self), port.pin))
		return(True) # let's use True as example


	def output(self, port, value):
		# do whatever you do to set output value for 'pin':
		print(">>> set output value:{} for pin {}::{}".format(value, repr(self), port.pin))

	
# add class to the IO class:		
IO.Chip = IOChip
# IO.Chip.Port = IOPort
		