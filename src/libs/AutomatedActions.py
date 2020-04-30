from .base import baseTriggerAction
import time

#
# AutomatedAction trigger action, can be assigned as trigger_action on Buttons/Solenoid 
#	
class AutomatedActions(baseTriggerAction):
	"""this dummy trigger really does nothing."""
	config_name = 'automated_action'
	trigger_actions = ['delay1sec', 'solenoid'] # solenoid|buzzer|whatever
	counter= 0
	default_status = False
	status = False
	
	
	def __init__(self):
		# read trigger_action from config or use the hardcoded default from the init argument.
		self.trigger_actions = self.config.get('trigger_actions', self.trigger_actions)
	
	def trigger(self):
		self.status = True				# update status
		
		self.logger.debug('{:s} trigger() [ {:s}]'.format(self.log_name, str(self.trigger_actions)))

		for trigger_action in self.trigger_actions:
			self.call_trigger_on_object(trigger_action)
		
		self.counter = self.counter + 1 # statistics
		self.status = False				# update status
	
	
	def call_trigger_on_object(self, trigger_action):
		# call trigger on destination hw (trigger_action)
		
		if dc.hw.get(trigger_action, None) is not None:
							
			# valid issubclass baseTriggerAction
			if not isinstance(dc.hw[ trigger_action ], baseTriggerAction):
				self.logger.error('Trigger error on {:s}: action {:s} is no valid baseTriggerAction.'.format(self.config_name, self.trigger_action))
				raise   Exception('Trigger error on {:s}: action {:s} is no valid baseTriggerAction.'.format(self.config_name, self.trigger_action))

			dc.hw[ trigger_action ].trigger()

		else:
			self.logger.error('Trigger error on {:s}: action not found.'.format(self.config_name))
			raise   Exception('Trigger error on {:s}: action not found.'.format(self.config_name))
	

#
# Delay trigger action, can be assigned as part of the automated actions
#	
class Delay1sec(baseTriggerAction):
	"""delays 1 seconds."""
	config_name = 'delay1sec'
	
	def trigger(self):
		self.logger.debug('{:s} trigger()'.format(self.log_name))
		time.sleep(1)
	
