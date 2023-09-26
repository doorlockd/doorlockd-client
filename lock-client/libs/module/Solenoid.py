import libs.Module as module
import libs.IOWrapper as IO
from libs.data_container import data_container as dc
import time
from libs.Events import State

logger = dc.logger
# import logging
# logger = logging.getLogger(__name__)


class Solenoid(module.BaseModule):
	
	def __init__(self, config={}):
		super().__init__(config)
		
		# initialize myself 
		self.io_output_name = config['io_output']

		# event
		self.event_name  = config.get('event', 'open_solenoid')

		self.time_wait  = float(config.get('time_wait', 2.4))

		self.state = State(value=False)
		
		# # TEST:
		# self.state.subscribe(lambda v: print("New Solenoid State value: ", v))
		
		self.event = None
		
	def setup(self):
		# grab io_port from dc.io_port
		try:
			self.io_output = dc.io_port[self.io_output_name]
		except Exception:
			logger.exception('Failed setup Module %s', self.__class__.__name__)
			dc.e.raise_event('abort_app', wait=True)
		

	def enable(self):
		# enable module
		try:
			self.io_output.setup(IO.OUTPUT)
		except Exception:
			logger.exception('Failed enable Module %s', self.__class__.__name__)
			dc.e.raise_event('abort_app', wait=True)

		if self.io_output.input():
			# note, some GPIO libs will pull value LOW on setup. this message is here just incase we catch this:
			self.io_output.output(IO.LOW)
			logger.warning("!!! Solenoid was open on startup (this might show up by error)) !!!, io_output=%s", self.io_output_name)

		# connect IO port to our state value
		# self.state = False -> self.io_output.output(IO.LOW)
		# self.state = True  -> self.io_output.output(IO.HIGH)
		self.state.set_logic( lambda v: bool(self.io_output.output(v) or v) )
				
		# connect event to our callback
		self.event = dc.e.subscribe(self.event_name, self.action_callback)
		
			
	def disable(self):
		# disable module
		# cancel event 
		if self.event:
			self.event.cancel()
		
		# set output low
		self.state.value = False

		# cancel state logic:
		self.state.set_logic(None)
		
		if hasattr(self, 'io_output') and self.io_output.has_output:
			self.io_output.output(IO.LOW)

			
	def teardown(self):
		# de-setup module
		# cleanup ports
		if hasattr(self, 'io_output'):
			self.io_output.cleanup()
		
		
	def action_callback(self, data={}):		
		# get lock
		# if self.io_output.input():
		if self.state.value:
			logger.info("open solenoid ignored: (already open)")
			self.state.wait_for(False) # block this thread until solenoid is closed
			return

		# log
		logger.info("open solenoid (time_wait: %.2f seconds)", self.time_wait)
		self.state.value = True		# open solenoid
		time.sleep(self.time_wait)	# wait
		self.state.value = False	# close solenoid
		


