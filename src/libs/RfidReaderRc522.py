from .base import DoorlockdBaseClass, dc, baseTriggerAction
from .tools import hwid2hexstr
import time
import threading

from pirc522.rfid import RFID

class RfidReaderRc522(DoorlockdBaseClass):
	# config_name required for DoorlockdBaseClass
	config_name = 'rfid_rc522'
	default_status = True
		
	# SPI dev (bus , device), IRQ and RST
	spi_bus = 1
	spi_device = 0
	pin_irq = "P9_15"
	pin_rst = "P9_23"
	
	# internals
	counter = 0				# nice for statistics
	rdr = None				# RFID interface object
	stop_loop = True		# tag_detect loop
	thread = None			# thread object
	
	
	def __init__(self, start_thread=True):
		
		# get config or defaults
		self.spi_bus = self.config.get('spi_bus', self.spi_bus)
		self.spi_device = self.config.get('spi_device', self.spi_device)
		self.pin_irq = self.config.get('pin_irq', self.pin_irq)
		self.pin_rst = self.config.get('pin_rst', self.pin_rst)

		self.default_status = self.config.get('default_status', self.default_status)
		
		self.hw_init()

		# start thread if self.default_status = True
		if start_thread:
			if self.default_status:
				self.start_thread()
	
	
	def hw_init(self):
		# hw_init RFID reader
		self.rdr = RFID(bus=self.spi_bus, device=self.spi_device, pin_irq=self.pin_irq, pin_rst=self.pin_rst)
				
		self.logger.info('Myfare RfidReaderRc522 starting up ({:s}).'.format(self.log_name))
		self.logger.info('Myfare RfidReaderRc522 spi(bus,dev)=({}, {}), irq ({}), rst ({}).'.format(self.spi_bus, self.spi_device, self.pin_irq, self.pin_rst))
	
	# is the thread loop running?
	@property
	def status(self):
		if isinstance(self.thread, threading.Thread):
			if self.thread.isAlive():
				return(True)
				
		# in all other cases: 
		return(False)
		
	# start/stop the thread loop.
	@status.setter
	def status(self, state):
		if state is self.status:
			self.logger.info('notice: {:s}: status update ignored ( status is already {:s})'.format(self.log_name, str(state)))
		else:	
			if state:
				self.start_thread()
			else:
				self.stop_thread()
	
			
	def start_thread(self):	
		if not self.status:
			self.thread = threading.Thread(target=self.run, args=())
			self.thread.daemon = True	# Daemonize thread
			self.thread.start()			# Start the execution
			self.logger.info('start_thread {:s}'.format(self.log_name))
			
		else:
			self.logger.info('notice: {:s}: start_thread, thread is already running '.format(self.log_name))
			
		
	
	def stop_thread(self):
		# stop the loop
		self.stop_loop = True
		# call interupt on rdr
		self.rdr.irq_callback('pin')
		self.logger.info('stop_thread {:s}'.format(self.log_name))
		
		
		 
	def callback_tag_detected(self, hwid, rfid_dev):
		'''Overwrite this callback method with your own.
			
		def callback_tag_detected(hwid, rdr):
			# hwid = [255,255,255,255,255,255]
			# rfid_dev = the calling RfidReaderRc522 Object 
		
			# lookup hwid in db
			# if has_access:
			# 	solenoid.trigger()
		
		'''
		self.logger.debug('{:s} callback_tag_detected({:s}).'.format(self.log_name, str(hwid)))
		# raise NotImplementedError('method callback_tag_detected not implemented')
		

	def run(self):
		'''threading run()'''
		self.logger.info('run detect loop started ({:s}).'.format(self.log_name))
		self.stop_loop = False
		dc.e.raise_event('rfid_ready') # when rfid starts detecting
		while not self.stop_loop:
			# self.logger.debug("...(re)starting io_wait_for_tag_detected()")
			self.io_wait_for_tag_detected()
		dc.e.raise_event('rfid_stopped') # when rfid is stopped detecting
			

	def io_wait_for_tag_detected(self):
		'''start RFID reader and wait , callback_tag_detected() is run when a tag is detected. 
		'''
		
		rdr = self.rdr
		rdr.wait_for_tag()
		(error, tag_type) = rdr.request()
		
		dc.e.raise_event('rfid_comm') # when there is any RFID communication
		
			

		if not error:
			self.logger.debug("Tag detected")

			(error, hwid) = rdr.anticoll()
			dc.e.raise_event('rfid_comm') # when there is any RFID communication
			
			if not error:
				self.logger.debug("HWID: " + str(hwid))
				# Select Tag is required before Auth
				
				self.callback_tag_detected(hwid, rdr)
				
				# track statistics
				self.counter = self.counter + 1
				
				# if not rdr.select_tag(uid):
				# for sector in range(0, 63):
				#	 rdr_dump_sector(rdr, sector, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], uid)

				# Always stop crypto1 when done working
				#rdr.stop_crypto()
			if error:
				dc.e.raise_event('rfid_comm_error') # when there is any RFID communication error 
				self.logger.debug('Error ' + self.__class__.__name__+ ': error return by rdr.anticoll :')



	def hw_exit(self):
		'''calling rdr.stop_crypto() and rdr.cleanup() '''
		self.logger.debug('cleanup ' + self.__class__.__name__+ ': calling rdr.stop_crypto() and rdr.cleanup()')
		
		# stop internal thread
		self.stop_thread()
		
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
		

class RfidActions(DoorlockdBaseClass):
	trigger_action = 'open_door'
	config_name = 'rfid_action'
	counter = 0

	def __init__(self):
		# get config or defaults
		self.trigger_action = self.config.get('trigger_action', self.trigger_action)
		
	
	def callback_tag_detected(self, hwid, rfid_dev):
		hwid_str = hwid2hexstr(hwid) # make hwid in hex string format

		if dc.api.lookup_detected_hwid(hwid_str):
			self.logger.info('{:s} hwid ({:s}) access alowed.'.format(self.log_name, hwid_str))
			dc.e.raise_event('rfid_access_allowed') # raise when rfid is access_allowed
			self.trigger()
		else:
			self.logger.info('{:s} hwid ({:s}) access denied.'.format(self.log_name, hwid_str))
			dc.e.raise_event('rfid_access_denied') # raise when rfid is access_denied, will folow by ..._fin in x seconds
			time.sleep(1)
			dc.e.raise_event('rfid_access_denied_fin') # raise when rfid is access_denied after sleeping x seconds.
			
		
		
	def trigger(self):		
		# raise trigger_action event:
		dc.e.raise_event(self.trigger_action) # raise configured trigger_action for rfid_action
		self.counter = self.counter + 1
