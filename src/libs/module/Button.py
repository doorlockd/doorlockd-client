import libs.IOWrapper as IO
from libs.data_container import data_container as dc
import time
from libs.Events import State, Events
import libs.Module as module


logger = dc.logger
# import logging
# logger = logging.getLogger(__name__)


class Button(module.BaseModule):
	
	def __init__(self, config={}):
		# init module.BaseModule
		super().__init__(config)
		# self.events = Events()
		
		# initialize myself 
		self.io_input_name = config['io_input']

		# event
		self.event_name  = config.get('event', 'button_pressed')

		# # id
		# self.button_id = "button_" + config.get('id')

	def setup(self):
		# grab io_port from dc.io_port
		try:
			self.io_input = dc.io_port[self.io_input_name]
		except Exception:
			logger.exception('Failed setup Module %s', self.__class__.__name__)
			dc.e.raise_event('abort_app', wait=True)
		

	def enable(self):
		# enable module
		try:
			self.io_input.setup(IO.INPUT)
		
			# EDGE event
			self.io_input.add_event_detect(IO.EDGE_FALLING, lambda : self.events.raise_event('pressed', {}) or dc.e.raise_event(self.event_name, {}) )

		except Exception:
			logger.exception('Failed enable Module %s', self.__class__.__name__)
			dc.e.raise_event('abort_app', wait=True)
				
			
	def disable(self):
		# disable module
		# remove event detect
		if hasattr(self, 'io_input'):
			self.io_input.remove_event_detect()
			
	def teardown(self):
		# de-setup module
		# cleanup ports
		if hasattr(self, 'io_input'):
			self.io_input.cleanup()
		
		
		
		