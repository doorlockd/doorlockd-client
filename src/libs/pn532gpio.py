

# 0x0e = writeGPIO
# 1st byte: x00  https://www.nxp.com/docs/en/user-guide/141520.pdf WriteGPIO
# 2nd byte: x82

# clf.device.chipset.command(0x0e, b'\x00\x82', 0.1)


# get GPIO mode:
# >>> clf.device.chipset.command(0x06, b'\xff\xf4\xff\xf5\xff\xfc\xff\xfd', 0.1)
# bytearray(b'\x07\x00\xff\x00')
# >>> clf.device.chipset.command(0x06, b'\x63\x28', 0.1)
# bytearray(b'\x00')

# AUX1 pin : see CIU_AnalogTest register (6328h) on https://www.nxp.com/docs/en/nxp/data-sheets/PN532_C1.pdf
# >>> clf.device.chipset.command(0x08, b'\x63\x28\x00', 0.1)
# bytearray(b'')
# >>> clf.device.chipset.command(0x08, b'\x63\x28\xb0', 0.1)

## https://www.nxp.com/docs/en/nxp/data-sheets/PN532_C1.pdf :
## P3 and P7  registers:
# where x is 3 or 7 and n is the bit index.
# At maximum 4 different controllable modes can be supported. These modes are defined with the following bits:
# • PxCFGA[n]=0 and PxCFGB[n]=0: Open drain
# • PxCFGA[n]=1 and PxCFGB[n]=0: Quasi Bidirectional (Reset mode)
# • PxCFGA[n]=0 and PxCFGB[n]=1: input (High Impedance)
# • PxCFGA[n]=1 and PxCFGB[n]=1: Push/pull output
# Px[n] is used to write or read the port value.
# Here is the list of the registers used for these GPIO configuration
# name, 	addr,	Description 
# P3CFGA	FCh 	Port 3 configuration
# P3CFGB	FDh		Port 3 configuration
# P3    	B0h		Port 3 value	
# P7CFGA 	F4h 	Port 7configuration
# P7CFGB	F5h 	Port 7configuration
# P7    	F7h 	Port 7 value

# ReadRegister
# (P3CFGA, P3CFGB) =  clf.device.chipset.command(0x06, b'\xff\xfc\xff\xfd', 0.1)
# (P7CFGA, P7CFGB) =  clf.device.chipset.command(0x06, b'\xff\xf4\xff\xf5', 0.1)
# WriteRegister: 
# write P7CFGA x03 , P7CFGB x04  === 70,71 Quasi Bidirectional; 72 input.
# clf.device.chipset.command(0x08, b'\xff\xf4\x03\xff\xf5\x04', 0.1)



class pn532Gpio():
	"""
	GPIO interface to the PN532 rfid device, connected using nfcpy
	
	"""
	clf = None

	# _state[field] = value     #  bit values  0x08  0x40  0x20  0x10  0x08  0x04  0x02  0x01
	_state = {'P3': b'\x00'[0],	#  bits: [change=1, None,  P35,  P34,  P33,  P32,  P31,  P30]
			  'P7': b'\x00'[0]}	#  bits: [change=1, None, None, None, None,  P72,  P71, None]

	# The field P3 contains the state of the GPIO located on the P3 port
	# The field P7 contains the state of the GPIO located on the P7 port

	# register dictionary, see hw_read_cfg() how it's populated
	_cfg = {} 
	
	# lookup dictionary with portname = [field, bit possition]
	_addr = {'p30': ['P3', 0x01],
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
		self._state['P3'] = raw_state[0]
		self._state['P7'] = raw_state[1]
		# self._state['I0I1'] = raw_state[2] 
		
	def hw_read_cfg(self):
		# initialize P3 and P7 dict
		self._cfg = {'P3': {}, 'P7': {}}
		
		# read registers
		result = clf.device.chipset.command(0x06, b'\xff\xfc\xff\xfd\xff\xf4\xff\xf5', 0.1)
		self._cfg['P3']['A'] = result[0] # P3CFGA FCh Port 3 configuration
		self._cfg['P3']['B'] = result[1] # P3CFGB FDh Port 3 configuration
		self._cfg['P7']['A'] = result[2] # P7CFGA F4h Port 7 configuration
		self._cfg['P7']['B'] = result[3] # P7CFGB F5h Port 7 configuration

	def hw_write_cfg(self):
		# WriteRegister: 
		# clf.device.chipset.command(0x08, [\xff + register address + value ] ... , 0.1)
		
		cmd = bytearray()
		# P3CFGA FCh Port 3 configuration
		cmd.append(0xff)
		cmd.append(0xfc) 
		cmd.append(self._cfg['P3']['A'])
		# P3CFGB FDh Port 3 configuration
		cmd.append(0xff)
		cmd.append(0xfd) 
		cmd.append(self._cfg['P3']['B'])
		# P7CFGA F4h Port 7 configuration
		cmd.append(0xff)
		cmd.append(0xf4) 
		cmd.append(self._cfg['P7']['A'])
		# P7CFGB F5h Port 7 configuration
		cmd.append(0xff)
		cmd.append(0xf5) 
		cmd.append(self._cfg['P7']['B'])
		
		result = self.clf.device.chipset.command(0x08, cmd, 0.1)
		
		return(result)		
		
		
	def cfg_gpio_get(self, port):
		"""
		Get config type for GPIO port

		return int value: 
			0: Open drain, 
			1: Quasi Bidirectional, 
			2: input, 
			3: Push/pull output
		"""
		# lookup port in addr[], get state byte and bit position value
		(field, mask) = self._addr[ port ]
		
		# get cfg if missing
		if not hasattr(self._cfg, field):
			self.hw_read_cfg()
		
		# At maximum 4 different controllable modes can be supported. These modes are defined with the following bits:
		# • PxCFGA[n]=0 and PxCFGB[n]=0: Open drain
		# • PxCFGA[n]=1 and PxCFGB[n]=0: Quasi Bidirectional (Reset mode)
		# • PxCFGA[n]=0 and PxCFGB[n]=1: input (High Impedance)
		# • PxCFGA[n]=1 and PxCFGB[n]=1: Push/pull output

		# boolean value for PxCFGA[n]
		pxcfga = self._cfg[ field ]['A'] | ~ mask& 255 == 255 
		# boolean value for PxCFGB[n]
		pxcfgb = self._cfg[ field ]['B'] | ~ mask& 255 == 255 
		
		# return value 0...4 [0: Open drain, 1: Quasi Bidirectional, 2: input, 3: Push/pull output]
		return((int(pxcfga) * 1) + (int(pxcfgb) * 2))
		
	def cfg_gpio_set(self, port, gpio_type, write=True):
		""" 
		gpio_type: int(0 ... 3)
		0: Open drain, 
		1: Quasi Bidirectional, 
		2: input, 
		3: Push/pull output
		
		use hw_write_cfg() to write changes to hardware.
		"""
		# lookup port in addr[], get state byte and bit position value
		(field, mask) = self._addr[ port ]

		# boolean value for PxCFGA[n] is 1st bit of gpio_type
		pxcfga = bool(gpio_type & 0b01)
		# boolean value for PxCFGB[n] is 2nd bit of gpio_type
		pxcfgb = bool(gpio_type & 0b10)


		# get cfg if missing
		if not hasattr(self._cfg, field):
			self.hw_read_cfg()

		if pxcfga:
			# set bit position value to 1
			self._cfg[ field ]['A'] |= mask
		else:
			# set bit position value to 0
			self._cfg[ field ]['A'] &= ~ mask

		if pxcfgb:
			# set bit position value to 1
			self._cfg[ field ]['B'] |= mask
		else:
			# set bit position value to 0
			self._cfg[ field ]['B'] &= ~ mask
			
		if(write):
			return self.hw_write_cfg()
			
		
	def commit(self):
		# WriteGPIO command = 0x0e
		result = self.clf.device.chipset.command(0x0e, bytearray([self._state['P3'], self._state['P7']]), 0.1)
		
		# reset 'change' bit
		self._state['P3'] &= ~0x80
		self._state['P7'] &= ~0x80
		
		# return what result we got.
		return(result)		
		

	def gpio_on(self, port, commit=True):
		"""set GPIO port on		
		example: gpio_on('p33') 
		
		Use commit=False if you have more GPIO updates, use commit(). 
		"""
		# lookup port in addr[], get state byte and bit position value
		(field, mask) = self._addr[ port ]
		# set bit position value to 1
		self._state[field] |= mask
		# update/change bit to 1
		self._state[field] |= 0x80
		
		# commit
		if(commit):
			return self.commit()
		
	def gpio_off(self, port, commit=True):
		"""set GPIO port off
		example: gpio_off('p33') 

		Use commit=False if you have more GPIO updates, use commit(). 
		"""
		# lookup port in addr[], get state byte and bit position value
		(field, mask) = self._addr[ port ]
		# set bit position value to 0
		self._state[field] &= ~mask
		# update/change bit to 1
		self._state[field] |= 0x80
		
		# commit
		if(commit):
			return self.commit()
		
		
	def gpio_toggle(self, port, commit=True):
		"""toggle GPIO , turn off when on and visa versa.
		example: gpio_toggle('p33') 
		
		Use commit=False if you have more GPIO updates, use commit(). 
		"""
		# lookup port in addr[], get state byte and bit position value
		(field, mask) = self._addr[ port ]
		# set bit position value to 1
		self._state[field] ^= mask
		# update/change bit to 1
		self._state[field] |= 0x80
		
		# commit
		if(commit):
			return self.commit()

	def gpio_get(self, port, no_cache=True):
		""" return True/False if GPIO port is 1/0  """
		
		# read current IO values
		if(no_cache):
			self.hw_read_state()
		
		# lookup port in addr[], get state byte and bit position value
		(field, mask) = self._addr[ port ]
		# return True if bit is set to 1
		return(self._state[field] | ~ mask & 255 == 255)
	#
	# #
	# # dev tests:
	# #
	# def set_p32_on(self):
	# 	# self._state_p3 |= 0x04
	# 	# self._state_p3 |= 0x80
	# 	self._state['P3'] |= 0x84
	#
	# def set_p32_off(self):
	# 	self._state['P3'] &= 0x04
	# 	self._state['P3'] |= 0x80
	#
	# def set_p32_toggle(self):
	# 	self._state['P3'] ^= 0x04
	# 	self._state['P3'] |= 0x80
	#
		
	# 
	def debug(self):
		print("DEBUG: P3 {0:08b}, P7 {1:08b}".format(self._state['P3'], self._state['P7']))
		

	def debug_info(self):
		"""
		some debug overview , handy when using bpython cli interface.
		"""
		print("bin   ReadGPIO P3 {0:08b}".format(self._state['P3']))
		print("bin   P3CFGA   P3 {0:08b}".format(self._cfg['P3']['A']))
		print("bin   P3CFGB   P3 {0:08b}".format(self._cfg['P3']['B']))

		print("bin   ReadGPIO P7 {0:08b}".format(self._state['P7']))
		print("bin   P7CFGA   P7 {0:08b}".format(self._cfg['P7']['A']))
		print("bin   P7CFGB   P7 {0:08b}".format(self._cfg['P7']['B']))
		
		GPIO_TYPE = ['Open drain', 'Quasi Bidirectional', 'input', 'Push/pull output']
		
		for p in ['p30', 'p31', 'p32', 'p33', 'p34', 'p35', 'p71', 'p71']:
			v = str(self.gpio_get(p))
			t = self.cfg_gpio_get(p)
			print ("GPIO port {} value {:5s} config: {}: {} ".format(
					p,
					v,
					t, GPIO_TYPE[t] ))