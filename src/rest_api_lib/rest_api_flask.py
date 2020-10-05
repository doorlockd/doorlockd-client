from flask.views import MethodView
from flask import make_response, jsonify, request, abort, redirect
import json

# from orator.exceptions.query import QueryException

#
# from https://flask.palletsprojects.com/en/1.1.x/views/#method-views-for-apis
#


#
# HTTP status codes: https://restfulapi.net/http-status-codes/
#
# define Python user-defined exceptions

class ApiErrorRespons(Exception):
	"""Class for passing dict objects, ready to be served as JSON"""
	def __init__(self, err, code=500):
		self.err = err;
		
		if(not isinstance(err,dict)):
			print("error:  ApiErrorRespons should have an dict as argument not", err);
			self.err = {'raw_message': str(err)}

		if('error' not in err):
			print("error:  ApiErrorRespons dict is missing the 'error' field", err);
			self.err = 'undefined'

		if('message' not in err):
			print("error:  ApiErrorRespons dict is missing the 'message' field", err);
			self.err = 'undefined'
			

class ApiItem(object):
	
	# def __getitem__(cls, x):
	# 	'''make ApiItem subscriptable'''
	# 	return getattr(cls, x, None)
	
	def to_dict(self):
		'''Likely you need to replace this method.'''
		return(self.get())

	def to_json(self, *args, **kwargs):
		'''json dumps this object.

		it calls self.to_dict() to get all attributes.
		replace the to_dict(self) method in your own class.
		'''
		return(json.dumps(self.to_dict(), *args, **kwargs))


class ApiList(object):
	def to_list(self):
		# empty list
		result = []
		
		# itterate over our items items 
		for item in self.get():
			# get item as dict.
			result.append(item.get())
			
		return(result)

	def to_json(self,  *args, **kwargs):
		'''json dumps this object.

		it calls self.to_list() to get all attributes.
		replace the to_dict(self) method in your own class.
		'''
		return(json.dumps(self.to_list(),  *args, **kwargs))


class RestApi(MethodView):
	read_only_attributes = []
	write_only_attributes = []

	need_auth = bool(False)
	need_validation = bool(False)
	need_defaults = bool(False)
	need_enforce_read_only = bool(False)
	need_enforce_write_only = bool(False)
	
	
	debug_mode = False
	# type casts = {'key': int}
    # type_casts = {}
	
	@classmethod
	def flask_add_rules(cls, uri_path, flask_app,  uri_path_id='<int:id>', pk='id', methods=['LIST','POST','GET', 'PUT', 'DELETE', 'PATCH']):
		'''add HTTP end_points for this RestApi class:
			class MyUsersRestApi(...,RestApi):
				...
		
			MyUsersRestApi.flask_add_rules('/users/', app)
		
			will add:
			# we use method 'LIST' to define the GET method to list all entries:
			app.route('/users/', methods=['GET']):
		
			# POST / create
			app.route('/users/', methods=['POST']):
		
			# GET, PUT, DELETE, PATCH (read, update, delete ...)
			app.route('/users/<int:id>', methods= [....]):
		
		'''
		# view class name 'as_view' => api_rest_ + uri_path (translate special chars?).
		view_class_name = 'api_rest_view_' + uri_path
		
		view_instance = cls.as_view(view_class_name)

		print('DEBUG: flask_add_rules: ', methods, uri_path)

		# copy methods to prevent updating the static value of this method
		my_methods = methods.copy()
		
		if 'LIST' in my_methods:
			flask_app.add_url_rule(uri_path, defaults={pk: None}, view_func=view_instance, methods=['GET',])
			my_methods.remove('LIST')
			# print('DEBUG: add_url_rule LIST:', uri_path)
			
		if 'POST' in methods:
			flask_app.add_url_rule(uri_path, view_func=view_instance, methods=['POST',])
			my_methods.remove('POST')
			# print('DEBUG: add_url_rule POST:', uri_path)

		# the rest of the methods ['GET', 'PUT', 'DELETE', 'PATCH']]
		if len(my_methods) != 0:
			flask_app.add_url_rule(uri_path+uri_path_id, view_func=view_instance, methods=my_methods)
			# print('DEBUG: add_url_rule ', my_methods , uri_path)
		
		

	def _call_get_http_auth(self):
		# if need_auth: read token or fail 401
		
		# check if we need it.
		if self.need_auth:
			return self.get_http_auth()
			

	def get_http_auth(self):
		raise NotImplementedError('implement get_http_auth in your own class')

		#
		# if 'Authorization' in request.headers:
		# 	auth = request.headers.get('Authorization')
		# 	print("FOUND: Auth (not implemented)", auth)
		# 	# return(auth)


			
			
	
	def _call_has_access(self, auth, method, model=None):
		if self.need_auth:
			return self.has_access(auth, method, model)
		
	def has_access(self, auth, method, model=None):
		raise NotImplementedError('implement has_access in your own class')
		
		# # auth : { uid:  , } (jwt payload)
		# # method :  GET/PUT/POST/DELETE/PATCH
		# # model : this item
		# # TODO: implement permision checks && aborts
		# print("WARNING: has_access not implemented. ",auth, method, model)
		
		
	
	def is_valid(self, model):
		# match with self.json_schema
		if self.need_validation:
			self.validator(model)
		
	def validator(self, model):
		'''implement an validation checks && aborts, don't forget to set need_validation''' 
		pass
		
		
	def _call_set_defaults(self, model):
		# call set defaults
		if self.need_defaults:
			self.set_defaults(model)
		
	def set_defaults(self, model):
		'''implement an set_defaults to add defaults to the model, don't forget to set need_defaults'''
		pass
		

	def enforce_write_only(self, obj):
		'''remove write-only attributes from data, and return new object'''
		if not self.need_enforce_write_only:
			return(obj)
			
		result = {}
		# make sure we have an iterable dict:
		data = self.make_dict(obj)
		

		for key in data:
			if key not in self.write_only_attributes:
				result[key] = data[key]
			else:
				print("DEBUG: enforced write-only for attribute", key)
		
		return(result)
			
	def enforce_read_only(self, old, new):
		'''raise error if any of the read-only attributes are changed in new compared with old.'''	
		if not self.need_enforce_read_only:
			return 
			
		for key in self.read_only_attributes:
			print ("DEBUG: read_only_attributes:", key)
			
			# if (old[key] != new[key]):
			if (self.x_getattr(old, key) != self.x_getattr(new, key) ):
				# read-only attribute is changed	
				print ("DEBUG: {} != {}".format(self.x_getattr(old, key), self.x_getattr(new, key) ))
				print ("DEBUG: {} != {}".format(type(self.x_getattr(old, key)), type(self.x_getattr(new, key)) ))
				error = {'error': 'read-only violation', 'message': "Cannot change read-only attribute: path '{}'.".format(key)}				
				self.response(error, 409)
			

	#
	# Datalayer methods 
	#
		
	def db_create(self, item):
		# create in data layer
		raise NotImplementedError('implement db_create in your own class')

	def db_update(self,id,item, old_data=None):
		# save/update in data layer
		raise NotImplementedError('implement db_update in your own class')

	def db_find_one(self, id):
		# find 1 in data layer
		raise NotImplementedError('implement db_find_one in your own class')

	def db_list(self):
		# get list from data layer
		raise NotImplementedError('implement db_list in your own class')

	def db_delete(self, id):
		# delete from data layer
		raise NotImplementedError('implement db_delete in your own class')
	   
	#
	# helper functions
	# 
	def make_json(self, obj):
		'''
		Orator models and collections are not serializable
		but do have .to_json methods we can use.
		
		use .to_json() method  if exists.
		othwerwise we use jsonify()
		'''
		# if it's a list , go into each item and call make_dict(item):
		if isinstance(obj, list):
			result = []
			# itterate list and call make_dict for each item
			for i in obj:
				result.append(self.make_dict(i))
			return(jsonify(result))
		
		# use .to_json if exists:
		if hasattr(obj, 'to_json'):
			return(obj.to_json(indent=4))
		else:
			# use jsonify 
			return(jsonify(obj))

	def make_dict(self, obj):
		'''
		Orator models and collections are not serializable
		but do have .to_dict(), .items methods we can use.
		
		use .to_dict method  if exists.
		othwerwise we use jsonify()
		'''
		
		# it's a dict:
		if isinstance(obj, dict):
			# print("DEBUG: it's already dict")
			return(obj)
		
		# use .to_dict if exists (Orator):
		if hasattr(obj, 'to_dict'):
			# print("DEBUG: make_dict: to_dict()")
			return(obj.to_dict())

		# we have no solution for this object:
		raise TypeError("object {}, don't know how to make dict of it.".format(str(obj)))

	
	def x_getattr(self, obj, key, default=KeyError):
		# is it a Dict
		if isinstance(obj, dict):
			# does it have the key: key
			if key in obj:
				return(obj[key])
			else:
				if default is KeyError:
					raise KeyError(key)
				else:
					return default
		
		# asume we can use getattr()
		else:
			if default is KeyError:
				return(getattr(obj, key))
			else:
				return(getattr(obj, key, default))

	def redirect(self, path, code=302):	
		resp = make_response(redirect(path), code)
		print ("DEBUG: redirect {}, {}".format(path, code))
		abort(resp)
		
	def response(self, obj, code=200, location=None):
		'''make json HTTP response of "object" with status "code" (default: 200) '''

		# response(True) -> HTTP 204 No Content; Location: ...
		if obj is True:
			self.response(None, 204, location)
	
		
		# short cut for :
		resp = make_response(self.make_json(obj), code, {'Content-Type': 'application/json'})

		if location:
			resp.headers['Location'] = location

		# DEBUG:
		if code != 200:
			print ("DEBUG: json response:", code, obj)
			

		abort(resp)
		
	
	#
	# type casting attributes
	#
	# def cast_attr(self, key, value):
	# 	''' Replace with your own:
	# 	cast attribute from json to internal python value.
	# 	like how the db layer handles it.'''
	# 	return(value)

	def cast_object(self, obj, instance=None):
		''' cast dict from json to internal python value. 
		like how the db layer handles it.
		'''
		#
		# result = {}
		# for key in obj:
		# 	result[key] = self.cast_attr(key, obj[key])
		# return result
		return obj
	
	
	#
	# HTTP routing to objects
	#
	def magic_parse_route(self, **kwargs):
		'''method is called by GET/PUT/POST/DELETE/PATCH. you can use it to set the envirement 
		to set it up for any nested/related object.  
		
		for example: 
		## ROUTE : /users/<int:user_id>/posts/<int:id> [...]
		# def magic_parse_route(self, **kwargs):
		# 	user_id = kwargs.get('user_id')
		# 	self._orator_model = User.find_or_fail(user_id).posts()
		
		'''
		# nothing_id = args['nothing_id']
		# self._orator_model = User.find_or_fail(nothing_id).rfidtags()
		# print("magic_parse_route: ", kwargs)
		pass
	#
	# HTTP methods:
	#
			
	def get_list(self):
		'''GET  : Read collection'''
		
		# get auth header (if needed)
		auth = self._call_get_http_auth()
		
		# check permision (if needed)
		self._call_has_access(auth, 'GET')
		
		# get items from data layer
		data = self.db_list()

		# enforce_write_only:
		for i, item in enumerate(data):
			data[i] = self.enforce_write_only(item)

		# serialize json, http 200
		self.response(data, 200)

	def get_item(self, id):
		'''GET  : Read single item'''
		
		# get auth header (if needed)
		auth = self._call_get_http_auth()
		
		# check permision (if needed)
		self._call_has_access(auth, 'GET')
		
		# get item from data layer
		data = self.db_find_one(id)

		# 404 not found 
		if data is None:
			error = {'error': 'not found', 'message': "..."}
			self.response(error, 404)

		# check permision for this item (if needed)
		self._call_has_access(auth, 'GET', data)
		
		# enforce write-only permisions
		result = self.enforce_write_only(data)
		
		# serialize json, http 200
		self.response(result, 200)

	def get(self, id, **kwargs):
		self.magic_parse_route(**kwargs)
		
		if id is None:
			return self.get_list()
		else:
			return self.get_item(id)
			
		
	def post(self, **kwargs):
		'''POST : Create single item'''
		
		# set env for nested/related objects
		self.magic_parse_route(**kwargs)

		# get auth header (if needed)
		auth = self._call_get_http_auth()
		
		# check permision (if needed)
		self._call_has_access(auth, 'GET')
		
		# get POST data from HTTP request
		new_item = request.get_json()		
		
		# add defaults if needed
		self._call_set_defaults(new_item)

		# check validation (if needed)
		self.is_valid(new_item)
			
		# do we have permision to create THIS item here
		self._call_has_access(auth, 'POST', new_item)

		# cast json values to python values
		new_item = self.cast_object(new_item)
				
		
		# create item in db layer 
		try:
			item = self.db_create(new_item)

		except ApiErrorRespons as e:
			print("error ", type(e.err),  e.err)
			self.response(e.err, e.code)
			
		except Exception as e:
			error = {'error': 'db error', 'message': str(e) }
			print(error)
			if self.debug_mode:
				raise(e)
				
			self.response(error, 500)

		# enforce write-only permisions for response
		result = self.enforce_write_only(item)
		
		print("DEBUG: item", item, result)

		# serialize json, http 200
		self.response(result, 200)
		

	def put(self, id, **kwargs):
		'''PUT  : Update single item'''		
		# set env for nested/related objects
		self.magic_parse_route(**kwargs)

		# get auth header (if needed)
		auth = self._call_get_http_auth()
		
		# check permision (if needed)
		# self._call_has_access(auth, 'PUT')
		
		# get POST data from HTTP request
		new_item = request.get_json()
		
		# add defaults if needed
		self._call_set_defaults(new_item)

		# check validation (if needed)
		self.is_valid(new_item)
				
		# check permision to update this item (if needed)
		self._call_has_access(auth, 'PUT', new_item)

		# get item from data layer
		old_item = self.db_find_one(id)

		# 404 not found
		if old_item is None:
			 error = {'error': 'not found', 'message': '...'}
			 self.response(error, 404)

		# # check permision to update this item (if needed)
		# self._call_has_access(auth, 'PUT', old_item)

		# cast json values to python values
		new_item = self.cast_object(new_item, old_item)
		# some how cast_object corrupts db_find_one... for orator
		# print("DEBUG old_item:" ,  self.db_find_one(id))
		
		
		# enforce read-only attributes
		self.enforce_read_only(old_item, new_item)


		# # orator only test:
		# old_item.update(new_item)
		# update item in db layer 
		try:
			item = self.db_update(id, new_item, old_item)
		except Exception as e:
			error = {'error': 'db error', 'message': str(e) }
			print(error)
			if self.debug_mode:
				raise(e)
				
			
			# display error / debug : raise(e)
			# raise(e)
			self.response(error, 500)

		# enforce write-only permisions for response
		result = self.enforce_write_only(item)
			
		# serialize json, http 201
		self.response(result, 201)


	def delete(self, id, **kwargs):
		'''DELETE : Delete single item'''		
		# set env for nested/related objects
		self.magic_parse_route(**kwargs)

		# get auth header (if needed)
		auth = self._call_get_http_auth()
		
		# check permision (if needed)
		self._call_has_access(auth, 'DELETE')
		
		try:
			result = self.db_delete(id)

				
		except Exception as e:
			error = {'error': 'db error', 'message': str(e) }
			print(error)
			if self.debug_mode:
				raise(e)
			
			self.response(error, 500)

		# not found:
		if result == 0:
			error = {'error': 'not found', 'message': '...'}
			print(error)
			self.response(error, 404)
			
		# serialize json, http 204
		# self.response(None, 204)
		self.response(True)
		

	def patch(self, id, **kwargs):
		'''PATCH : update single item using jsonpatch'''
		return('Patch not implemented..')

