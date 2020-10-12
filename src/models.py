from orator import Model
from orator.orm import morph_to, morph_many, belongs_to, has_one, has_many, belongs_to_many, mutator, accessor
import jsonpatch

# for password hashing: hashlib, base64 and os:
import hashlib
import os
import base64

# 
# get current logged on uid for our ChangelogObserver
#
from flask import  request, has_request_context
import jwt
def get_unverified_current_uid():
	'''Get uid from jwt token out of the flask request. '''
	# 
	if not has_request_context():
		return None
		
	if not 'Authorization' in request.headers:
		return None
		
	auth_header = request.headers.get('Authorization')
	
	# get jwt token from header 'Bearer ##########TOKEN######'
	token = auth_header.split(" ")[1]
	
	# get payload from jwt token 
	payload = jwt.decode(token, verify=False)
	
	if 'uid' in payload:
		# print ("Found uid in payload ", payload)
		return(payload['uid'])
	else:
		print ('Error: get_unverified_current_uid(): No uid in jwt payload!')
		return(None)



class Changelog(Model):
	__timestamps__ = False
	__fillable__ = ['action', 'changelogger_type', 'changelogger_id', 'diff', 'now', 'prev','user_id' ]
	__dates__ = ['now', 'prev']
	__casts__ = {'diff': 'dict'}

	@morph_to
	def changelogger(self):
		return

	@belongs_to
	def user(self):
		return User
	

class ChangelogObserver(object):
	'''ChangelogObserver makes diff's of all changes made on an orator.Model.
	
	On the Models:
	class ExampleModel(Model):
		# hide the changelogs attribute when exporting to dict or json
		__hidden__ = ['changelogs']
	
		# define the childs 'ON DELETE CASCADE' in the Model
		# We do this here using the orator.Model.delete() method so the ChangelogObserver can keep track of all deleted itmes.
		__on_delete_cascade__ = ['child_model', 'child_collection', ... ]
	
		# register the ChangelogObserver class
		@classmethod
		def _boot(cls):
			super(AuthType2, cls)._boot()
			# connect our Observer
			cls.observe(ChangelogObserver(cls))
	
		# setup the changelogs relation attribute:
		@morph_many('changelogger')
		def changelogs(self):
			return Changelog
		
	
	'''
	ignore_keys = []
	dict_type = 'table_dict'
	# table_dict = dict like flat table structure , like db.table looks ( dict / list are (json) strings )
	# model_dict = dict like model, with casted attributes like dict / list / boolean 
	changelog_attribute = 'changelogs'


	def __init__(self, model_cls, changelog_attribute='changelogs', ignore_keys = [] ):
		self.ignore_keys = ignore_keys
		self.changelog_attribute = changelog_attribute
		
		# do not diff timestamps 
		if model_cls.__timestamps__:
			self.ignore_keys.append(model_cls.get_created_at_column(model_cls))
			self.ignore_keys.append(model_cls.get_updated_at_column(model_cls))
			
		# do not diff the primary key:
		self.ignore_keys.append(model_cls.get_key_name(model_cls))
		
		# print("DEBUG: _ignore_keys:", self.ignore_keys)
		
		
	# tabledict = dict like flat table structure , like db.table looks ( dict / list are (json) strings )
	def cast_original_to_tabledict(self, obj):		
		cast = obj.get_original()
		return(cast)
				
	def cast_current_to_tabledict(self, obj):		
		cast = {}
		for k in obj.get_attributes().keys():
			v = obj.get_raw_attribute(k)
			if (isinstance(v, bool)):
				# cast booleans into 1 / 0 
				cast[k] =  int(v)
			else:
				cast[k] = v
			
		return(cast)

	# modeldict = dict like model, with casted attributes like dict / list / boolean 
	def cast_original_to_modeldict(self, obj):		
		cast = {}
		for k in obj.get_attributes().keys():
			if k in obj.__casts__.keys():
				cast[k] = obj._cast_attribute(k, obj.get_original(k))
			else:
				cast[k] = obj.get_original(k)
		return(cast)
				
	def cast_current_to_modeldict(self, obj):		
		cast = {} 
		for k in obj.get_attributes().keys():
			if k in obj.__casts__.keys():
				cast[k] = obj._cast_attribute(k, obj.get_raw_attribute(k))
			else:
				cast[k] = obj.get_raw_attribute(k)
		return(cast)
				

	def make_history(self, obj, action):
		if(self.dict_type == 'model_dict'):
			orig = self.cast_original_to_modeldict(obj)
			newo = self.cast_current_to_modeldict(obj)
		else:
		# if(self.dict_type == 'table_dict'):
			orig = self.cast_original_to_tabledict(obj)
			newo = self.cast_current_to_tabledict(obj)
			
		print("DEBUG: ", self.dict_type)
		print("DEBUG: orig:", orig)
		print("DEBUG: newo:", newo)

		
		# set our timestamps
		if obj.__timestamps__:
			now = obj.as_datetime(newo.get(obj.get_updated_at_column()))
			if obj.get_updated_at_column() in orig:
				prev = obj.as_datetime(orig.get(obj.get_updated_at_column()))
			else:
				prev = None
				
		else:
			now = obj.as_datetime('now')
			prev = None

		
		# remove keys we ignore in our histroy
		for k in self.ignore_keys:
			orig.pop(k, None)
			newo.pop(k, None)
			
		# jsonpatch	   
		patch = jsonpatch.JsonPatch.from_diff(orig, newo).patch
				
				
		# user_id / User object from current auth session.
		user_id = get_unverified_current_uid()
		
		print('DEBUG: changelog user_id :', user_id)
		
		# changelog_attribute
		h1 = obj.changelogs().create(diff=patch, action=action, prev=prev, now=now, user_id=user_id)
		
		# print(h1.to_json(indent = 4))
		# print('changelog:', h1.action, h1.changelogger_type, h1.changelogger_id )
		print("DEBUG: changelog({}): '{}'  {}({}) ".format( h1.id, h1.action, h1.changelogger_type, h1.changelogger_id ))
		for diff in h1.diff:
			print('DEBUG: changelog diff:', diff )
		# print('END')
			
		
	
	def created(self, obj):
		self.make_history(obj, 'create')

	def updated(self, obj):
		self.make_history(obj, 'update')

	def deleted(self, obj):
		self.make_history(obj, 'delete')
		
	def deleting(self, obj):
		'''Cascade delete child models. 
		
		define the childs 'ON DELETE CASCADE' in the Model using:
		__on_delete_cascade__ = ['child_model', 'child_collection']
		
		list items can either be a Collection of multiple childs, or a single child relation.
		
		We do this here using the orator.Model.delete() method so the ChangelogObserver can keep track of all deleted itmes.
		If we let the sql database do it by ON DELETE CASCADE, the ORM wouldn't know.
		'''
		# collect our childs:
		childs = []
		for relation in getattr(obj,'__on_delete_cascade__', []):
			# append single child  or 'None'
			childs.append(getattr(obj, relation, None))

			# extend with list of childs or an empty list if not found.
			childs.extend(getattr(getattr(obj, relation, None), 'items', []))

		# itterate over childs and delete() if it is a Model class
		for child in childs:
			if isinstance(child, Model):
				child.delete()
				
				
	def restored(self, obj):
		self.make_history(obj, 'restore')

	



class User(Model):
	__fillable__ = ['email', 'password_hash','password_plain','is_disabled']
	# __appends__ = ['password_plain']
	__hidden__ = ['changelogs']	
	__casts__ = {'is_disabled': 'bool'}

	@classmethod
	def _boot(cls):
		super(User, cls)._boot()
		# connect our Observer
		cls.observe(ChangelogObserver(cls))
					
	# @accessor
	# def password_plain(self):
	# 	return("None")
	
	# @password_plain.mutator
	@mutator
	def password_plain(self, value):
		# encode password hash.

		if value is not None:
			# print("DEBUG: update password ", value)
			self.set_raw_attribute('password_hash', self.do_hash_password(value))

	# @password_hash.mutator
	@mutator
	def password_hash(self, value):
		# update password_hash.

		if value is not None:
			# print("DEBUG: update password_hash ", value)
			self.set_raw_attribute('password_hash', value)


	def do_hash_password(self, plain_password, salt=None):
		'''returns an base85 encoded password hash to store in your database.
		
		The hash consists of salt(32) + sha256 hash of an utf-8 encoded plain_password.
		'''
				
		# gerate random salt if not supplied
		if not salt:
			salt = os.urandom(32)
		
		# encode password using (random) 32 char length salt, sha256, and 100000x 
		password_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
		
		# encode base85 combined string of salt + hash
		return(base64.b85encode(salt + password_hash).decode('utf-8'))
		
	
	def do_verify_password(self, plain_password, stored_hash=None):
		'''Verify password against stored hashed password.
		
		returns True or False
		'''

		if not stored_hash:
			stored_hash = self.password_hash
		
		# stored_hash is base85 encoded and has 32 char length salt prepended 
		try:
			salt = base64.b85decode(stored_hash)[:32]
			# password_hash = stored_hash[:32]
		except ValueError:
			print("DEBUG: password hash base85 encoding error.")
			return(False)
			
		
		# return True | False
		return(stored_hash == self.do_hash_password(plain_password, salt))
		
		
		
	# def __repr__(self):
	#	 return '<User %r>' % self.email

	@morph_many('changelogger')
	def changelogs(self):
		'''morph_many Collection of Changelog models: tracks all changes to this object'''
		return Changelog

	
class Tag(Model):
	__fillable__ = ['hwid', 'description', 'is_disabled']
	__hidden__ = ['changelogs']
	__casts__ = {'is_disabled': 'bool'}
	

	@classmethod
	def _boot(cls):
		super(Tag, cls)._boot()
		# connect our Observer
		cls.observe(ChangelogObserver(cls))
		
		# connect post create event: delete all UnknownTags by this hwid:
		cls.created(lambda tag: UnknownTag.where('hwid', tag.hwid ).delete())
		
		
				
	# def __repr__(self):
	#	 return '<Tag %r>' % self.hwid

	@morph_many('changelogger')
	def changelogs(self):
		'''morph_many Collection of Changelog models: tracks all changes to this object'''
		return Changelog


class UnknownTag(Model):
	__fillable__ = ['hwid']
	
	# # no changelogs for this table:
	#
	#	 __hidden__ = ['changelogs']
	#
	#
	#	 @classmethod
	#	 def _boot(cls):
	#		 super(UnknownTag, cls)._boot()
	#		 # connect our Observer
	#		 cls.observe(ChangelogObserver(cls))
	#
	#
	#	 # def __repr__(self):
	#	 #	 return '<Tag %r>' % self.hwid
	#
	#	 @morph_many('changelogger')
	#	 def changelogs(self):
	#		 '''morph_many Collection of Changelog models: tracks all changes to this object'''
	#		 return Changelog
