from .base import DoorlockdBaseClass
import threading

from pirc522.rfid import RFID

class RfidReaderRc522(threading.Thread, DoorlockdBaseClass):
	# config_name required for DoorlockdBaseClass
	config_name = 'rfid_rc522'
		
	# SPI dev (bus , device)
	spi_bus = 1
	spi_device = 0

	
	# RFID interface object
	rdr = None
	
	def __init__(self):
		
		# get config or defaults
		self.spi_bus = self.config.get('spi_bus', 1)
		self.spi_device = self.config.get('spi_device', 0)
		
		# hw_init RFID reader
		self.rdr = RFID(bus=self.spi_bus, device=self.spi_device)
		
		self.logger.info('Myfare RfidReaderRc522 starting up ({:s}).'.format(self.log_name))
		
		
	def callback_tag_detected(self, hwid, rdr):
		'''Overwrite this callback method with your own.
			
		def callback_tag_detected(hwid, rdr):
			# hwid = [255,255,255,255,255,255]
			# rdr = RFID Object 
		
			# lookup hwid in db
			# if has_access:
			# 	solenoid.trigger()
		
		'''
		self.logger.debug('{:s} callback_tag_detected({:s}).'.format(self.log_name, str(hwid)))
		# raise NotImplementedError('method callback_tag_detected not implemented')
		

	def run(self):
		'''threading run()'''
		while True:
		    self.wait_for_key()
			

	def wait_for_key(self):
		rdr = self.rdr
		rdr.wait_for_tag()
		(error, tag_type) = rdr.request()
		# self.ui_pulse_comm()

		## commmented out , to verbose...., perhaps no error here?.
		#if error:
		#   self.logger.debug("Can't detect RFID tag, rdr.request error")
			

		if not error:
			self.logger.debug("Tag detected")

			(error, hwid) = rdr.anticoll()
			# self.ui_pulse_comm()
			if not error:
				self.logger.debug("HWID: " + str(hwid))
				# Select Tag is required before Auth
				
				self.callback_tag_detected(hwid, rdr)
				# if not rdr.select_tag(uid):
				# for sector in range(0, 63):
				#	 rdr_dump_sector(rdr, sector, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], uid)

				# Always stop crypto1 when done working
				#rdr.stop_crypto()
			if error:
				# self.ui_show_comm_error()
				self.logger.debug('Error ' + self.__class__.__name__+ ': error return by rdr.anticoll :')



	def hw_exit(self):
		'''calling rdr.stop_crypto() and rdr.cleanup() '''
		self.logger.debug('cleanup ' + self.__class__.__name__+ ': calling rdr.stop_crypto() and rdr.cleanup()')

		# Always stop crypto1 when done working
		self.rdr.stop_crypto()
		
		# Calls GPIO cleanup
		self.rdr.cleanup()

		
	def io_read_data_block(self, hwid, tag_secret, sector ):
		''' read doorkey from rfid tag by hwid, tag_secret, and sector id (1 ... 15)  '''
		if not rdr.select_tag(hwid):
			# Authenticate for sector (first block of sector)
			if not rdr.card_auth(rdr.auth_a, int(sector * 4 + 0 ), tag_secret, hwid):

				# calculate block number (first block of sector) 
				block = sector * 4 + 0
	
				# read block 
				(error, data) = rdr.read(block)
				

		# Always stop crypto1 when done working
		rdr.stop_crypto()

		return(error, data) 
		

		


