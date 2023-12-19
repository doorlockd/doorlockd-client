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

		# permanent open:
		self.allow_permanent_open = bool(config.get('allow_permanent_open', False))
		self.event_name_toggle_permanent_open = str(config.get('event_toggle_permanent_open', 'toggle_permanent_open'))
		self.permanent_open_state = State(value=False)
		self.io_output_name_permanent_open_ui_led = config.get('io_output_permanent_open_ui_led', None)
		
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
		
		# if not None
		if self.io_output_name_permanent_open_ui_led:
			try:
				self.io_output_permanent_open_ui_led = dc.io_port[self.io_output_name_permanent_open_ui_led]
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

		# permanent_open: connect event to our callback
		self.event_toggle_permanent_open = dc.e.subscribe(self.event_name_toggle_permanent_open, self.toggle_permament_open_callback )

		# permanent_open ui_led
		if hasattr(self, 'io_output_permanent_open_ui_led'):
			try:
				self.io_output_permanent_open_ui_led.setup(IO.OUTPUT)
				self.io_output_permanent_open_ui_led.output(IO.LOW)
			except Exception:
				logger.exception('Failed enable Module %s', self.__class__.__name__)
				dc.e.raise_event('abort_app', wait=True)

		
			
	def disable(self):
		# disable module
		# cancel event 
		if self.event:
			self.event.cancel()
		
		if self.event_toggle_permanent_open:
			self.event_toggle_permanent_open.cancel()

		# set output low
		self.state.value = False

		# cancel state logic:
		self.state.set_logic(None)
		
		if hasattr(self, 'io_output') and self.io_output.has_output:
			self.io_output.output(IO.LOW)

		if hasattr(self, 'io_output_permanent_open_ui_led') and self.io_output_permanent_open_ui_led.has_output:
			self.io_output_permanent_open_ui_led.output(IO.LOW)

			
	def teardown(self):
		# de-setup module
		# cleanup ports
		if hasattr(self, 'io_output'):
			self.io_output.cleanup()
		
		if hasattr(self, 'io_output_permanent_open_ui_led'):
			self.io_output_permanent_open_ui_led.cleanup()
		
	def action_callback(self, data={}):
		"""
		Open Solenoid for self.time_wait seconds.
		"""
		if self.permanent_open_state.value:
			logger.info("open solenoid ignored: (permanent open)")
			self.state.wait_for(False, self.time_wait) # block this thread for x seconds or when solenoid is closed
			return

		if self.state.value:
			logger.info("open solenoid ignored: (already open)")
			self.state.wait_for(False) # block this thread until solenoid is closed
			return

		# Open solenoid for x seconds:
		logger.info("open solenoid (time_wait: %.2f seconds)", self.time_wait)
		self.state.value = True		# open solenoid
		time.sleep(self.time_wait)	# wait
		self.state.value = self.permanent_open_state.value # close solenoid/switch to permanent state.
		

	def toggle_permament_open_callback(self, data={}):
		# only switch config setting on if your hardware supports pemanent_open:
		if not self.allow_permanent_open:
			logger.warn("allow_permanent_open disabled: toggle permanent open/close is disabled.")
			return

		# switch state:
		self.permanent_open_state.value = not self.permanent_open_state.value
		logger.info(f"permanent_open_state switched to {self.permanent_open_state.value}.")

		# set UI LED if defined
		if hasattr(self, 'io_output_permanent_open_ui_led') and self.io_output_permanent_open_ui_led.has_output:
			self.io_output_permanent_open_ui_led.output(self.permanent_open_state.value)

		# sync hardware:
		self.state.value = self.permanent_open_state.value
		logger.info(f"hardware synced to new permanent_state {self.state.value}.")


