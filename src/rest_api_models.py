from rest_api_lib.rest_api_orator import RestApiOrator
from rest_api_lib.rest_api_jsonschema import JsonSchemaForRestApi
from rest_api_login import JwtForRestApi


from models import *


#
# API /api/user
#
# implement: UserRestApi.flask_add_rules('/api/users/', app)
class UserRestApi(JwtForRestApi, JsonSchemaForRestApi, RestApiOrator):
	_orator_model = User
	def __init__(self):
		self._read_json_schema('schema/schema.users.json')
		self.need_auth = True
		self.need_validation = True
		self.need_defaults = True
		self.need_enforce_read_only = True
		self.need_enforce_write_only = True

	pass
	
#
# API /api/tag
#
# implement: TagRestApi.flask_add_rules('/api/tag/', app)
class TagRestApi(JwtForRestApi, JsonSchemaForRestApi, RestApiOrator):
	_orator_model = Tag
	def __init__(self):
		self._read_json_schema('schema/schema.tags.json')
		self.need_auth = True
		self.need_validation = True
		self.need_defaults = True
		self.need_enforce_read_only = True
		self.need_enforce_write_only = True
		
	pass

#
# API /api/unkown_tag
#
# implement:  UnknownTagRestApi.flask_add_rules('/api/unknown_tag/', app)
class UnknownTagRestApi(JwtForRestApi, JsonSchemaForRestApi, RestApiOrator):
	_orator_model = UnknownTag
	def __init__(self):
		self._read_json_schema('schema/schema.unknown_tags.json')
		self.need_auth = True
		self.need_validation = True
		self.need_defaults = True
		self.need_enforce_read_only = True
		self.need_enforce_write_only = True
		
	pass


#
# API /api/changelogs/<type>/<id>/<id> (UITprobeersel)
#
# implement:  ChangelogRestApi.flask_add_rules('/api/changelogs/<string:model_type>/<int:model_id>/', app, methods=['LIST', 'GET'])
class ChangelogRestApi(JwtForRestApi, JsonSchemaForRestApi, RestApiOrator):
	_orator_model = None
	
	def __init__(self):
		self.need_auth = True
	
	# 	self.need_enforce_read_only = True
	# 	self.need_enforce_write_only = True

	def magic_parse_route(self, **kwargs):
		model_type = kwargs.get('model_type')
		model_id = kwargs.get('model_id')
		self._orator_model = Changelog.where('changelogger_type', model_type).where('changelogger_id', model_id)



#
# Api singleobject:
#
from rest_api_lib.rest_api_singleobject import RestApiSingleObject
# schema.dummy.json

# define dummy object 
class dummyObject():
	some_name = "bla bla"
	_some_number = 42
	
	@property
	def some_number(self):
		self._some_number = 1 + self._some_number
		return(self._some_number)
	
	@some_number.setter
	def some_number(self, number):
		self._some_number = number

	
# init dummy object
dummy_obj = dummyObject()

# create rest api wrapper for dummy obj
class DummyRestApi( RestApiSingleObject):
	def __init__(self):
		self._object = dummy_obj
		self._read_json_schema('schema/schema.dummy.json')
		# self.need_auth = True
		self.need_validation = True
		# self.need_defaults = True
		self.need_enforce_read_only = True
		self.need_enforce_write_only = True


# create rest api wrapper for dummy obj
def create_api_for_object(any_object=None, json_schema=None, urlpath=None, app=None):
	class AnySingleObjectRestApi( RestApiSingleObject):
		def __init__(self):
			print ("DEBUG: setting _object any object:", type(any_object), any_object)
			self._object = any_object

			self._read_json_schema(json_schema)

			# self.need_auth = True
			self.need_validation = True
			# self.need_defaults = True
			self.need_enforce_read_only = True
			# self.need_enforce_write_only = True
		
	# run self.flask_add_rules()
	if urlpath is not None:
		AnySingleObjectRestApi.flask_add_rules(urlpath, app, methods=['GET', 'PUT'])
	
	return(AnySingleObjectRestApi)


#
# Add all above Api classes with routes to Flask
#
def add_to_flask(app):
	UserRestApi.flask_add_rules('/api/users/', app)
	TagRestApi.flask_add_rules('/api/tags/', app)
	UnknownTagRestApi.flask_add_rules('/api/unknown_tags/', app)
	ChangelogRestApi.flask_add_rules('/api/changelogs/<string:model_type>/<int:model_id>/', app, methods=['LIST', 'GET'])

	import rest_api_login
	app.add_url_rule('/api/login/', view_func=rest_api_login.login_endpoint , methods=['POST'])
	app.add_url_rule('/api/refresh_token/', view_func=rest_api_login.token_refresh_endpoint , methods=['POST'])
	
	# dummy object
	DummyRestApi.flask_add_rules('/api/single/dummy', app, methods=['GET', 'PUT'])
	
	# any_object, json_schema, urlpath=None, app=None, methods=['GET', 'PUT']):
	# create_api_for_object(dummy_obj, 'schema/schema.dummy.json').flask_add_rules('/api/hw/dummy', app, methods=['GET', 'PUT'])
	create_api_for_object(dummy_obj, 'schema/schema.dummy.json', '/api/hw/dummy', app)
	
	
