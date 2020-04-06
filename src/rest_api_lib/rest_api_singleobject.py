# from flask.views import MethodView
# from flask import make_response, jsonify, request, abort
from .rest_api_flask import RestApi 
from .rest_api_jsonschema import JsonSchemaForRestApi
from flask import jsonify

#
# nieuw ideee:
# removes need for obj -> to_json conversion
#  db_find_one -> return read only dict
#  db_update -> return sets write-only attrib.
#

# remove get -> item , rather set dummy id=1 or so.
# replace flask_add_rules to just fit PUT/GET requests.


class RestApiSingleObject(JsonSchemaForRestApi, RestApi):
	_object = None

	@classmethod
	def flask_add_rules(cls, uri_path, flask_app,  uri_path_id='<int:id>', pk='id', methods=['LIST','POST','GET', 'PUT', 'DELETE', 'PATCH']):
		'''add HTTP end_points for this RestApi SingleObject class:
			class MyUsersRestApi(...,RestApi):
				...
		
			MySettingsObject.flask_add_rules('/api/settings', app)
							
			# will add:
			# GET, PUT, PATCH (read, update, ...)
			app.route('/api/settings', methods= [....]):
		
			!!! this is a SingleObject:
			 methods LIST POST DELETE are ignored.
			 uri_path_id is ignored
			 pk is ignored
		
			# # we use method 'LIST' to define the GET method to list all entries:
			# app.route('/users/', methods=['GET']):
			#
			# # POST / create
			# app.route('/users/', methods=['POST']):
		
		'''
		# view class name 'as_view' => api_rest_ + uri_path (translate special chars?).
		view_class_name = 'api_rest_view_' + uri_path
		
		view_instance = cls.as_view(view_class_name)

		print('DEBUG: flask_add_rules: ', methods, uri_path)

		# copy methods to prevent updating the static value of this method
		my_methods = methods.copy()
		#
		# if 'LIST' in my_methods:
		# 	flask_app.add_url_rule(uri_path, defaults={pk: None}, view_func=view_instance, methods=['GET',])
		# 	my_methods.remove('LIST')
		# 	# print('DEBUG: add_url_rule LIST:', uri_path)
		#
		# if 'POST' in methods:
		# 	flask_app.add_url_rule(uri_path, view_func=view_instance, methods=['POST',])
		# 	my_methods.remove('POST')
		# 	# print('DEBUG: add_url_rule POST:', uri_path)

		# the rest of the methods ['GET', 'PUT', 'DELETE', 'PATCH']]
		# ignore DELETE
		# my_methods.remove('DELETE')
		
		# for SingleObject we use a dummy value of 1
		if len(my_methods) != 0:
			flask_app.add_url_rule(uri_path,defaults={pk: 1}, view_func=view_instance, methods=my_methods)
			# print('DEBUG: add_url_rule ', my_methods , uri_path)
		
		
	# overwrite get to always return get_item
	def get(self, id, **kwargs):
		self.magic_parse_route(**kwargs)
		return self.get_item(None)

	# overwrite make_dict
	def make_dict(self, obj):
		#if obj is already dict , return it , it might be an error message:
		if type(obj) is dict:
			return(obj)
		
		#make dict from object
		d = {}
		for attr in self.all_attributes:
			d[attr] = getattr(obj, attr, None)			
		return(d)
		
	# overwrite make_json	
	def make_json(self, obj):
		d = self.make_dict(obj)
		return(jsonify(d))
	
	def db_find_one(self, id):
		# find 1 in data layer
		# return single object
		return(self._object)

	# def db_list(self):

	# def db_create(self, item):

			
	def db_update(self, id, new_item, old_item=None):
		
		# if old_item is None:
		# 	old_item = self.db_find_one(id)
			
		for attr in self.all_attributes:
			if attr not in self.read_only_attributes:
				# set/update attribute:
				try:
					setattr(self._object, attr, new_item[attr])
				except Exception as e:
					# TODO
					print ("ERROR: db_update on object:", self._object, attr, new_item[attr])
					raise(e)	
		# catch errror?
		return(self._object)	
	
	# def db_delete(self, id):
		
	# def cast_object(self, object, instance=None):
	# 	# cast incomming json into python object similar like orator does from sql:
	#
	# 	# change time-date into pendulum objects:
	# 	# we need to initialize the model to get_dates()
	#
	# 	if instance is None:
	# 		#instance = self._orator_model()
	# 		## hack to workarround issuse with TypeError: 'HasMany' object is not callable
	# 		instance = self._orator_model.find_or_new(None)
	#
	# 	# get date attributes on this model
	# 	dates = instance.get_dates()
	#
	# 	# cast our dates
	# 	for key in dates:
	# 		if key in object:
	# 			object[key] = instance.as_datetime(object[key])
	#
	# 	return(object)
		
		
