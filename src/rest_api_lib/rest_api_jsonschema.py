from jsonschema import validate, ValidationError, FormatChecker
import json
# access conig and logger using our data container
from libs.data_container import data_container as dc

class JsonSchemaForRestApi(object):
	'''adds json_schema functionality to your RestApi:
	- validation
	- set default values
	- enforces read-only and write-only permisions.
	'''
	
	#
	# set_schema_from_file
	def _read_json_schema(self, json_schema_file):
		'''set schema from file '''
		# print ("debug: read schema file", json_schema_file)
		with open(json_schema_file) as json_file:
		    self.json_schema  = json.load(json_file)
					
	
	def _parse_json_schema(self, json_schema):
		'''set schema from json string '''
		self.json_schema = json.loads(json_schema)
		
	
	@property
	def json_schema(self):
		'''get schema from dict'''
		return(self.__json_schema_dict)
	
	@json_schema.setter
	def json_schema(self, json_schema_dict):
		'''set schema from dict'''
		# set our json_schema 
		self.__json_schema_dict = json_schema_dict
	
		# set our read-only attributes
		self.read_only_attributes = self.__get_read_only_attrib_form_schema(json_schema_dict)
		# set our write-only attributes
		self.write_only_attributes = self.__get_write_only_attrib_form_schema(json_schema_dict)
		# set all attributes
		self.all_attributes = self.__get_attrib_from_schema(json_schema_dict)
		
	def __get_attrib_from_schema(self, schema_dict=None):
		'''get all attributes from json_schema  '''
		if schema_dict is None:
			schema_dict = self.json_schema
			
		attributes = []
		for key, propertie in schema_dict['properties'].items():
			attributes.append(key)
		return(attributes)
		
		
	def __get_read_only_attrib_form_schema(self, schema_dict=None):
		'''get all attributes from json_schema marked as readeOnly '''
		if schema_dict is None:
			schema_dict = self.json_schema
			
		attributes = []
		for key, propertie in schema_dict['properties'].items():
			if 'readOnly' in propertie and propertie['readOnly']:
				attributes.append(key)
		return(attributes)

	def __get_write_only_attrib_form_schema(self, schema_dict=None):
		'''get all attributes from json_schema marked as writeOnly '''
		if schema_dict is None:
			schema_dict = self.json_schema
			
		attributes = []
		for key, propertie in schema_dict['properties'].items():
			if 'writeOnly' in propertie and propertie['writeOnly']:
				attributes.append(key)
		return(attributes)


	def __get_defaults_form_schema(self, schema_dict=None):
		'''get all defaults from json_schema as {key: value} dict.'''
		if schema_dict is None:
			schema_dict = self.json_schema
			
		defaults = {}
		for key, propertie in schema_dict['properties'].items():
			if 'default' in propertie:
				defaults[key] = propertie['default']
		return(defaults)

	#
	# json-schema RestApi impementations:
	#

	#
	# validation methods
	#
	def validator(self, model):
		
		try:
			validate(instance=model, schema=self.json_schema, format_checker=FormatChecker())
		except ValidationError as e:
			# catches only first error.
			error = {}
			error['type'] = 'validation'
			error['error'] = 'validation'
			# pointer '.' or path '/' --> error['fields'][key] = 'error message'
			error['fields'] = { '.'.join(e.path): e.message }
			# error['message'] = e.message
			error['message'] = "{}, {}".format('.'.join(e.path), e.message) # bit more userfriendly 
						
			# print( '------validation-error:---------------' )
			# print( 'error: ', json.dumps(error, indent=3))
			# print( '--------------------------------------' )
			# print( 'raw: ', e )
			# print( '--------------------------------------' )

			dc.logger.debug("------validation-error:---------------")
			dc.logger.debug("validation-error: json-dumps(error): {}".format(json.dumps(error, indent=3)))
			dc.logger.debug("--------------------------------------")
			dc.logger.debug("validation-error: raw: {}".format(str(e)))
			dc.logger.debug("--------------------------------------")
			
			# HTTP response
			self.response(error, 400)

	# 
	# set defaults
	#
	def set_defaults(self, model):
		
		# itterate over default values and check if attribute exist in model:
		for key, propertie in self.json_schema['properties'].items():
			if 'default' in propertie:
				if key not in model: 
					# we have a missing attribute:
					dc.logger.debug("jsonschema: set missing key: '{}' = '{}'".format( key, propertie['default']))
					model[key] = propertie['default']
			
	