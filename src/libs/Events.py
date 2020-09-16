

class Events(object):
	#	 
	# _events[event_id][] = { prio=5, f_action=function, ... }
	#
	_events = {}
				
	def subscribe(self, event_id, f_action, prio=50):
		'''subscribe to an event by 'event_id', and callback f_action. optional priority lowest priority first.
		if the callback function (f_action) returns False no more events in the loop are executed.'''
	
		# init event_id array if missing
		if event_id not in self._events:
			self._events[event_id] = []
			
		# add subscription
		self._events[event_id].append({'prio': prio, 'f_action': f_action})
	
	def unsubsrcibe(self, event_id, f_action):
		'''remove subscription'''
		if event_id not in self._events:
			# nothing to do
			return

		for idx, event in reversed(list(enumerate( self._events[event_id] ))):
			if event['f_action'] == f_action:
				del(self._events[event_id][idx])
	
	def raise_event(self, event_id, data={}):
		'''raise an event by event_id, and pass any data to the callback functions.'''
		if event_id not in self._events:
			# nothing to do
			return
			
		# for event in self._events[event_id]:
		for event in sorted(self._events[event_id], key=lambda event: event['prio']):
			if event['f_action'](data) is False:
				# stop executing action
				print("Eventloop '{}' stopped by function '{}'.".format(event_id, event['f_action']))
				break
				
