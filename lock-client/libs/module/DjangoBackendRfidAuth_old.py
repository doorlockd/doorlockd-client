import requests
import simplejson as json
import threading
import datetime
import time
import hashlib
import os

# import logging
# logger = logging.getLogger(__name__)

from libs.data_container import data_container as dc
logger = dc.logger


class ApiError(BaseException):

	def __init__(self, message, resp=None):
			self.message = message
			self.resp = resp

			if self.resp is not None:
				try:
					self.json = resp.json()
					print('inside ApiError', json.dumps(self.json,  indent=4))
				except ValueError:
					print('No JSON !!!!',  resp.content)
				except AttributeError:
					print('No JSON !!!!',  resp.content)
			else:
				print("NO response data to display...")

class LogStats:
	def __init__(self, parent,  precision=0, sync_interval=None):
		self.parent = parent
		self.table_key_last_seen = []
		self.table_unknown_key = []
		self.lock = threading.Lock()
		
		self.precision = precision # in seconds. will be devided in exact intervals since epoch
		self.sync_interval = sync_interval if sync_interval else self.precision

		self.limit_post_entries = 1024

		# direct push sync
		self.direct_push_on_add = False
		self.next_sync = self.get_timestamps_now_begin_end(self.sync_interval)[2]
	
	
	def get_timestamps_now_begin_end(self, precision=None):
		'''Get timestamps for logging: (now, begin, end)
			now: is now
			begin: is beginning of 'privacy friendly' time window set by self.precision
			end: is end of 'privacy friendly' time window set by self.precision
		'''
		precision = precision if precision else self.precision
		t_now = datetime.datetime.now().timestamp()
		
		# int(timestamp / precision) * precision ==> timestamp of begin of this interval.
		if precision > 1:
			# precision is not 0
			t_begin = int(t_now / precision) * precision
			# set end off interval 
			t_end = ((int(t_now / precision) + 1) * precision) - 0.000001
		else:
			t_begin = t_now
			# precision = 0
			t_end = t_now
		
		return t_now, t_begin, t_end
			
	def add(self, key, known_key):
		# get privacy friendly timestamps, now , begin, end
		t_now, t_begin, t_end = self.get_timestamps_now_begin_end()
		
		r = {}
		r['key'] = str(key)
		r['count'] = 1
		
		# UnknownKey
		if not known_key:
			# set timestamp
			r['timestamp'] = datetime.datetime.fromtimestamp(t_now).isoformat()
			
			# save:
			with self.lock:
				try: 
					# find existing one if exist
					item = next(item for item in self.table_unknown_key if item['key'] == key)
					item['count'] += r['count']
					item['timestamp'] = r['timestamp']
				except:	
					# add new
					self.table_unknown_key.append(r)
	
		
		# Key -> LastSeen table with obfuscated timestamp	
		else:
			r['timestamp_begin'] = datetime.datetime.fromtimestamp(t_begin).isoformat()
			r['timestamp_end'] = datetime.datetime.fromtimestamp(t_end).isoformat()
		
			with self.lock:		
				try: 
					# find existing one if exist
					item = next(item for item in self.table_key_last_seen if item['key'] == key)
					item['count'] += r['count']
					item['timestamp_begin'] = r['timestamp_begin']
					item['timestamp_end'] = r['timestamp_end']
				except:	
					# add new
					self.table_key_last_seen.append(r)
		
		if self.direct_push_on_add or not known_key:
			self.try_sync()
		
	def try_sync(self, flush=False):
		t_now,t_begin,t_end = self.get_timestamps_now_begin_end()
		# always sync unknown keys if available:
		with self.lock:		
			if len(self.table_unknown_key) != 0:
				self.api_sync_unknownkeys()
			
			# knwon keys, only sync periodicly	
			if len(self.table_key_last_seen) != 0:
				if flush or self.next_sync < t_now:
					self.api_sync_keys_last_seen(flush)

			if len(self.table_key_last_seen) == 0:
				self.next_sync = self.get_timestamps_now_begin_end(self.sync_interval)[2]
			
	def api_sync_unknownkeys(self):
		unknownkeys = []
		for uk in self.table_unknown_key[:self.limit_post_entries]:
			unknownkeys.append(uk)
		
		try:
			resp = self.parent.request_post(f'/api/lock/log.unknownkeys', {'unknownkeys': unknownkeys})
			logger.debug(f"DEBUG: resp: {resp}")
		except Exception as e:
			logger.warning(f"Network down?: api_sync_unknownkeys failed: {e.__class__.__name__}: {e}")
			return
				
		
		logger.info(f"unknownkeys synchronized: {len(resp.get('saved'))}")
		
		# remove saved items from our list
		for item in resp.get('saved'):
			logger.debug(f"remove item: {item}")
			self.table_unknown_key.remove(item)
		
	def api_sync_keys_last_seen(self, flush=False):
		keys_last_seen = []
		t_now = datetime.datetime.now()
		
		# collect entries to sync
		for k in self.table_key_last_seen[:self.limit_post_entries]:
			# if timestamp_end is newer then now: it's time to sync:
			keys_last_seen.append(k)

		if keys_last_seen:
			try:
				resp = self.parent.request_post(f'/api/lock/log.keys_last_seen', {'keys_last_seen': keys_last_seen})
				logger.debug(f"DEBUG: resp: {resp}")
			except Exception as e:
				logger.warning(f"Network down?: api_sync_keys_last_seen failed: {e.__class__.__name__}: {e}")
				return
		
		
			logger.info(f"keys_last_seen synchronized: {len(resp.get('saved'))}")
			
			# remove saved items from our list
			for item in resp.get('saved'):
				logger.debug(f"remove item: {item}")
				self.table_key_last_seen.remove(item)
		

		
	def dump(self):
		print("table_unknown_key:")
		for r in self.table_unknown_key:
			print(json.dumps(r)	)

		print("table_key_last_seen")
		for r in self.table_key_last_seen:
			print(json.dumps(r)	)
			
		print(f"next sync in : {int(self.next_sync - self.get_timestamps_now_begin_end()[0])} seconds")	


class BackendApi():
	
	def __init__(self, token, api_url, offline_file=None, log_unknownkeys=True, log_stats_precision=3600*24*7, log_sync_interval=None):
		self.lockname = 'lockname' # deprecated.
		
		self.lock_disabled = True # disable lock on startup
		self.synchronized = False # we are not synchronized at startup
		# log unknownkeys
		self.log_unknownkeys = log_unknownkeys
		
		self.lock = threading.Lock()
		
		# self.keys = [False]
		self.keys = {'false': {'ruleset':[]}}
		# self.disabled = False
		
		self.api_url = api_url
		self.headers = {}
		self.headers['Authorization'] = f'Bearer {token}'

		# log_stats_precision = 3600*24*7 = 1 week
		self.log_stats = LogStats(self, precision=log_stats_precision, sync_interval=log_sync_interval)
				
		self.auto_sync_secs = 6
		self.auto_sync_event = threading.Event()
		
		# if offline_file
		self.offline_file = offline_file
		self.tmp_offline_file = lambda : f'temp_{self.offline_file}'
		
		# offline_file doesn't exist???
		if self.offline_file is not None and not os.path.isfile(self.offline_file):
			logger.critical(f"!!! STRANGE: Missing offline file '{self.offline_file}' !!!")
		
			
	def setup(self):	
		# try load_from_file 
		self.load_from_file()
					
		# try start back_ground_sync
		self.start_background_sync()
			
		# just a warning, since we 	
		if self.lock_disabled is True:
			logger.warning("at end setup(): lock is disabled or never synchronised, lookup() and last-seen logging ignored.")
		
	def dump(self):
		for k in self.keys.keys():
			print(f" * {k}:")
			if self.keys[k]['ruleset']:
				for r in self.keys[k]['ruleset']:
					print(f'   - {r}' )
			
	def load_from_file(self):
		if self.offline_file is not None:
			logger.info(f"read keys database from file: '{self.offline_file}';")
			with self.lock:
				try:
					# open json file
					with open(self.offline_file, "r") as json_file:
						# Reading from file
						data = json.load(json_file)
					
						# simply overwrite dict:
						self.keys = data.get('keys')
						logger.info(f"read keys database, entries: '{len(self.keys)}' keys loaded.")
						logger.info(f"read keys database, hash   : '{self.keys_hash()}' ")
							
						# lock_disabled, or if missing guess the answer on the numer of keys.
						self.lock_disabled = data.get('lock_disabled', not bool(len(self.keys)))
						logger.info(f"read lock disabled: .")
						
				except Exception as e:
					logger.critical(f"!!! Failed to load_from_file failed!: {e.__class__.__name__}: {e}")
		else:
			logger.debug(f"offline_file is not sprecified: '{self.offline_file}'")
			
														
	def save_to_file(self):
		
		
		if self.offline_file is not None:
			logger.info(f"write keys database to file '{self.tmp_offline_file()}'")
			with self.lock:
				try:
					data = {}
					data['keys'] = self.keys
					data['lock_disabled'] = self.lock_disabled
					
					# tmp file shouldn't exist, rename to _cleanup 
					if os.path.isfile(self.tmp_offline_file()):
						logger.critical(f"!! Found unexpected tmp file '{self.tmp_offline_file()}' ")
						# os.rename(self.tmp_offline_file(), self.del_offline_file)
						os.remove(self.tmp_offline_file())
					
					# write to tmp file
					with open(self.tmp_offline_file(), 'w') as json_file:
						json.dump(data, json_file)
					
					# rename tmp file 
					if os.path.isfile(self.offline_file):
						os.remove(self.offline_file)
						
					os.rename(self.tmp_offline_file(), self.offline_file)
					
					logger.info(f"written keys database to file : '{self.offline_file}';")
					logger.info(f"written keys database, entries: '{len(self.keys)}' keys, '{os.path.getsize(self.offline_file)}' bytes.")
					logger.info(f"written keys database, hash   : '{self.keys_hash()}' ")
					
				except Exception as e:
					logger.critical(f"!!! Failed to save_to_disk: {e.__class__.__name__}: {e}")	
		else:
			logger.debug(f"offline_file is not sprecified: '{self.offline_file}'")
					
			

	def start_background_sync(self):
		# self.auto_sync_thread = threading.Thread(target=auto_sync_target, args=(self,))
		# self.auto_sync_thread.start()
		
		def auto_sync_target(self, event):
			"""threading target"""
	
			logger.info("DEBUG: start auto_sync_target")
			while(not event.is_set()):
				self.api_sync()
				time.sleep(self.auto_sync_secs)
	
			logger.info("DEBUG: auto_sync_target stopped!")	
	
		def auto_long_pull_sync_target(self, event):
			"""threading target"""
	
			logger.debug("DEBUG: start auto_long_pull_sync_target")
			while(not event.is_set()):
				try: 
					self.long_pull_events()
				except Exception as e:
					logger.info(f"long poll suspended for 60seconds  due to {e.__class__.__name__}: {e}")
					event.wait(timeout=60) # use event.wait instead of time.sleep.
					
			
			logger.debug("DEBUG: auto_long_pull_sync_target stopped!")	
		

		with self.lock:
			# are we already running?
			if hasattr(self, 'auto_sync_thread') and self.auto_sync_thread.isAlive():
				return self.auto_sync_thread

			self.auto_sync_event.clear()
			self.auto_sync_thread = threading.Thread(target=auto_long_pull_sync_target, args=(self,self.auto_sync_event))
			self.auto_sync_thread.start()
			
			return self.auto_sync_thread
		
	
	def stop_background_sync(self, join=False):
		with self.lock:
			if not self.auto_sync_event.is_set():
				logger.debug(f"DEBUG: auto_sync will stop... {self.auto_sync_event.is_set()}")	
				# print("self.auto_sync", self, self.auto_sync)
				self.auto_sync_event.set()
		
		if join:
			logger.debug(f"DEBUG: join thread... {getattr(self, 'auto_sync_thread', 'not-set')}")	
			if hasattr(self, 'auto_sync_thread'):
				self.auto_sync_thread.join()
		
		# self.auto_sync_thread	

	def cleanup(self):		
		# order background thread to stop
		self.stop_background_sync()
		
		# try sync last_seen and unknown_keys
		self.log_stats.try_sync(flush=True)

		# join thread to 
		self.stop_background_sync(join=True)
		
		# offline_file doesn't exist???
		if self.offline_file is not None and not os.path.isfile(self.offline_file):
			logger.critical(f"!!! STRANGE: Missing offline file '{self.offline_file}' !!!")
		
		

	# def __del__(self):
	# 	logger.debug(f"DEBUG: '{self}.__del__()' called!")
	# 	# self.cleanup()

	def keys_hash(self):
		return hashlib.new('SHA256', json.dumps(self.keys, sort_keys=True).encode('utf-8')).hexdigest()
		

	def acl_parse_rule(self, rule):
		now = datetime.datetime.now()
		
		after = rule.get('after', None)
		before = rule.get('before', None)
		weekdays = rule.get('weekdays', [])
		time_start = rule.get('time_start', None)
		time_end = rule.get('time_end', None)
		#
		# rules of this rules (self, not child/parent)
		#

		# false if after newer than now
		if after is not None:
			if datetime.datetime.fromisoformat(after) > now:
				return False, "after newer than now"

		# false if before older than now
		if before is not None: 
			if datetime.datetime.fromisoformat(before) < now:
				return False, "before older than now"

		# false if is now.weekday() is not in weekdays 
		# if rule.weekdays is not None and now.weekday() not in rule.weekdays:
		if now.weekday() not in weekdays:
			return False, "today not in weekdays"

		# false if now.time is before time_start
		if time_start is not None:
			if  now.time() < datetime.time.fromisoformat(time_start):
				return False, "now is before time_start"

		# false if now.time is after time_end
		if time_end is not None:
			if  now.time() > datetime.time.fromisoformat(time_end):
				return False, "now is after time_end"	
	
		# nothing return false so we are OK
		return True, "nothing failed"
		
	
	def acl_has_access(self, hwid):
		# ruleset = self.keys.get(key,{}).get('ruleset',[])
		ruleset = self.keys[hwid]['ruleset']
		
		for rule in ruleset:
			logger.debug(f"DEBUG: { len(ruleset) },  {rule}")
			(acces, reason) = self.acl_parse_rule(rule)
			if acces is True:
				return (acces, reason)
			
		# no condition return true 
		return False, "no condition in ruleset returned true"
				
	def lookup(self, key):
		key = key.lower() # lowercase this key
		
		if self.lock_disabled is True:
			msg = "Warning: lock disabled or never synchronised, lookup() and last-seen logging ignored."
			logger.warning("Warning: lock disabled or never synchronised, lookup() and last-seen logging ignored.")
			return False, msg
			
		# lookup key in access list:
		if key not in self.keys:
			has_access, msg = False, 'Not found'
			known_key = False
		else:
			has_access, msg = self.acl_has_access(key)
			known_key = True

		# keep last_seen list
		if known_key or (not known_key and self.log_unknownkeys):
			self.log_stats.add(key, known_key)
		else:
			logger.debug("Logging is disabled by log_unknownkeys.")	
		
		return has_access, msg
	

		
		
	
	def request_post(self, path, data={}):
		url = self.api_url + path
		
		logger.debug(f"DEBUG POST:  {data}")
		resp = requests.post(url, json=data , headers=self.headers)

		if resp.status_code != 200:
			# This means something went wrong.
			raise ApiError('POST {}/ {}'.format(url ,resp.status_code), resp)
			
		return(resp.json())
		
			
	def long_pull_events(self):
		long_pull = requests.get(f'{self.api_url}/doorlockdb/api/lock/{self.lockname}/long_pull_events', headers=self.headers, stream=True)
				
		for event_line in long_pull.iter_lines(chunk_size=1):
			logger.debug(f"EVENT: {datetime.datetime.isoformat(datetime.datetime.now())} event_line: {event_line}")
			
			# check self.auto_sync for exit:
			if self.auto_sync_event.is_set():
				logger.debug(f"EVENT: {datetime.datetime.isoformat(datetime.datetime.now())} -- STOP AUTO_SYNC --")
				return 
			
			# remove empty line
			if  event_line == b'': 
				continue
				
			line = json.loads(event_line)
			# we have an event:
			if(line.get('event') == 'sync'):
				# sync keys:
				self.api_sync()
			
			
			# try sync last_seen and unknown_keys
			self.log_stats.try_sync()
			
			
			# initial sync: incase we havn't synchronized (when the client is just started.):
			if not self.synchronized:
				self.api_sync()
				
			
			
		logger.debug(f"EVENT: {datetime.datetime.isoformat(datetime.datetime.now())} -- DISCONNECTED --")
			
					
	def api_sync(self):
		"""sync with backend.
		"""
		
		max_loop = 3 # 
		
		with self.lock:
			#
			# check if we are up to date
			#
			keys_hash = self.keys_hash()
			resp = self.request_post(f'/api/lock/sync.keys', {'keys_hash': keys_hash})
			logger.debug(f"DEBUG: resp: {resp}")

			# show message in logs
			self.lock_disabled = bool(resp.get('disabled', False))
			if self.lock_disabled == True:
				logger.warning ("Warning: lock is disabled")
				
			# keys: -> update 
			# while 'keys' in resp:
			self.synchronized = bool(resp.get('synchronised', False))
			while self.synchronized is not True:	
				if max_loop <= 0:
					logger.warning("max loop detected, aborting sync action for now... and oppperate like nothing happend")
					logger.debug("info keys:", self.keys)
					return()
				

				# simply overwrite dict:
				self.keys = resp.get('keys')
				

				resp = self.request_post(f'/api/lock/sync.keys', {'keys_hash': self.keys_hash()})				
				logger.debug(f"DEBUG: resp: {resp}")
				
				# update synchronized
				self.synchronized = bool(resp.get('synchronised', False))
				
				# show message in logs
				self.lock_disabled = resp.get('disabled', False)
				if self.lock_disabled == True:
					logger.warning("Warning: lock is disabled")
				
				max_loop = max_loop -1 # decrement our loop counter



			# synchronized 
			if self.synchronized is True:
				logger.info(f"Info: we are synchronized. (hash: '{self.keys_hash()}')")
			else:	
				# some error
				if 'error' in resp:
					# something went wrong: 
					raise Exception(f"Error: error:{resp.get('error')}")
				else:
					# something went wrong without even an error message:
					raise Exception("Some fatal error, we don't understand:", resp)
		
		# if hash changed, save changes to file	
		if self.keys_hash() != keys_hash:
			self.save_to_file()
		
		



class DjangoBackendRfidAuth:
	def __init__(self, config={}):

		# init BackendApi with config:
		#
		#[module.rfid_auth]
		# type = "DjangoBackendRfidAuth"
		# token=
		# api_url= 
		# offline_file=None
		# log_unknownkeys=True
		# log_stats_precision=3600*24*7
		# log_sync_interval=None

		# token=token, api_url=api_url, offline_file=None, log_unknownkeys=True, log_stats_precision=3600*24*7, log_sync_interval=None
		kwargs = config.copy()
		del(kwargs['type']) # delete unwanted argument
		self.api=BackendApi(**kwargs)

		# set rfid_auth in global data container, so that self.has_access is available.
		dc.rfid_auth = self

	def setup(self):
		self.api.setup()
	
	def enable(self):
		self.api.start_background_sync()

	def disable(self):		
		self.api.stop_background_sync()
		
	def teardown(self):
		self.api.cleanup()
		
		
	def has_access(self, hwid_str):
		''' lookup detected hwid, 
			
		'''
		# lookup hwid in db
		access, msg = self.api.lookup(hwid_str)
		logger.debug(f'RFID KEY lookup({hwid_str}: access={access} : {msg}')
		return(access)
			
