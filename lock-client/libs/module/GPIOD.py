import libs.Module as module
import libs.IOWrapper as IO
from libs.data_container import data_container as dc
logger = dc.logger


import libs.IOWrapper.gpiod



class GPIOD(module.BaseModule):
	
	def __init__(self, config={}):
		# initialize myself 
		super().__init__(config)

		# use GPIOD interface
		io_gpiod = IO.gpiod.IOChip()

		# io_export , config:
		#
		# 
		for k in config['io_export'].keys():
			logger.info("export io name: '%s', port: '%s' (limit_direction=%s, active_low=%s, bias=%s, debounce_us=%s)", k, 
						config['io_export'][k]['port'],
						config['io_export'][k].get('limit_direction', None), 
						config['io_export'][k].get('active_low', False),
						config['io_export'][k].get('bias', None),
						int(config['io_export'][k].get('debounce_us', 0)))

			port = config['io_export'][k]['port']
			
			# translate limit_direction into IO.* enum value
			limit_direction = config['io_export'][k].get('limit_direction', None)
			if limit_direction is not None:
				limit_direction = getattr(IO, limit_direction)

			active_low = config['io_export'][k].get('active_low', False)

			# translate bias into IO.* enum value
			bias = config['io_export'][k].get('bias', None)
			if bias is not None:
				bias = getattr(IO, bias)
			
			# debounce_period in microseconds
			debounce_us = int(config['io_export'][k].get('debounce_us', 0))
			
			dc.io_port[k] = io_gpiod.Port(port, limit_direction=limit_direction, active_low=active_low, bias=bias, debounce_us=debounce_us)

	def setup(self):
		#setup module
		pass
			
	def enable(self):
		# enable module
		pass
		
	def disable(self):
		# disable module
		pass
		
	def teardown(self):
		#de-setup module
		pass
