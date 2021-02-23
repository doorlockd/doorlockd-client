

# 0x0e = writeGPIO
# 1st byte: x00  https://www.nxp.com/docs/en/user-guide/141520.pdf WriteGPIO
# 2nd byte: x82

# clf.device.chipset.command(0x0e, b'\x00\x82', 0.1)


# get GPIO mode:
# >>> clf.device.chipset.command(0x06, b'\xff\xf4\xff\xf5\xff\xfc\xff\xfd', 0.1)
# bytearray(b'\x07\x00\xff\x00')
# >>> clf.device.chipset.command(0x06, b'\x63\x28', 0.1)
# bytearray(b'\x00')


# AUX1 pin : https://www.nxp.com/docs/en/user-guide/141520.pdf
# >>> clf.device.chipset.command(0x08, b'\x63\x28\x00', 0.1)
# bytearray(b'')
# >>> clf.device.chipset.command(0x08, b'\x63\x28\xb0', 0.1)



class pn532Gpio():
	"""
	GPIO interface to the PN532 rfid device, connected using nfcpy
	
	"""
	clf = None
	# #                      	#  bit values  0x08  0x40  0x20  0x10  0x08  0x04  0x02  0x01
	state = {'P3': b'\x00'[0],	#  bits: [change=1, None,  P35,  P34,  P33,  P32,  P31,  P30]
			 'P7': b'\x00'[0]}	#  bits: [change=1, None, None, None, None,  P72,  P71, None]

	# The field P3 contains the state of the GPIO located on the P3 port
	# The field P7 contains the state of the GPIO located on the P7 port


	
	# lookup dictionary with portname = [state_byte, bit_possition]
	addr = {'p30': ['P3', 0x01],
			'p31': ['P3', 0x02],
			'p32': ['P3', 0x04],
			'p33': ['P3', 0x08],
			'p34': ['P3', 0x10],
			'p35': ['P3', 0x20],
			'p71': ['P7', 0x02],
			'p72': ['P7', 0x04]}
	
	def __init__(self, clf, hw_read_state=False):
		# set Contact Less Frontend. PN532
		self.clf = clf
		
		# read current state from hardware
		if (hw_read_state):
			self.hw_read_state()


	def hw_read_state(self):
		# ReadGPIO command = 0x0c
		raw_state =  self.clf.device.chipset.command(0x0c, b'', 0.1)
		self.state['P3'] = raw_state[0]
		self.state['P7'] = raw_state[1]
		self.state['I0I1'] = raw_state[2] 
		

	def commit(self):
		# WriteGPIO command = 0x0e
		self.clf.device.chipset.command(0x0e, bytearray([self.state['P3'], self.state['P7']]), 0.1)
		
		# reset 'change' bit
		self.state['P3'] &= ~0x80
		self.state['P7'] &= ~0x80
		

	def gpio_on(self, port, commit=True):
		"""set GPIO port on		
		example: gpio_on('p33') 
		
		Use commit=False if you have more GPIO updates, use commit(). 
		"""
		# lookup port in addr[], get state byte and bit position value
		(state, bit) = self.addr[ port ]
		# set bit position value to 1
		self.state[state] |= bit
		# update/change bit to 1
		self.state[state] |= 0x80
		
		# commit
		if(commit):
			self.commit()
		
	def gpio_off(self, port, commit=True):
		"""set GPIO port off
		example: gpio_off('p33') 

		Use commit=False if you have more GPIO updates, use commit(). 
		"""
		# lookup port in addr[], get state byte and bit position value
		(state, bit) = self.addr[ port ]
		# set bit position value to 0
		self.state[state] &= bit
		# update/change bit to 1
		self.state[state] |= 0x80
		
		# commit
		if(commit):
			self.commit()
		
		
	def gpio_toggle(self, port, commit=True):
		"""toggle GPIO , turn off when on and visa versa.
		example: gpio_toggle('p33') 
		
		Use commit=False if you have more GPIO updates, use commit(). 
		"""
		# lookup port in addr[], get state byte and bit position value
		(state, bit) = self.addr[ port ]
		# set bit position value to 1
		self.state[state] ^= bit
		# update/change bit to 1
		self.state[state] |= 0x80
		
		# commit
		if(commit):
			self.commit()

	#
	# #
	# # dev tests:
	# #
	# def set_p32_on(self):
	# 	# self.state_p3 |= 0x04
	# 	# self.state_p3 |= 0x80
	# 	self.state['P3'] |= 0x84
	#
	# def set_p32_off(self):
	# 	self.state['P3'] &= 0x04
	# 	self.state['P3'] |= 0x80
	#
	# def set_p32_toggle(self):
	# 	self.state['P3'] ^= 0x04
	# 	self.state['P3'] |= 0x80
	#
		
	# 
	def debug(self):
		print("DEBUG: P3 {0:08b}, P7 {1:08b}, I0I1 {2:08b}".format(g.state['P3'], g.state['P7'], g.state['I0I1']))