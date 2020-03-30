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


	# overwrite get to always return get_item
	def get(self, id, **kwargs):
		self.magic_parse_route(**kwargs)
		return self.get_item(None)

	# overwrite make_dict
	def make_dict(self, obj):
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
			
		# TODO: get attributes from json_schema ...
		for attr in self.all_attributes:
			# set/update attribute:
			self._object.attr = new_item[attr]
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
		
		
