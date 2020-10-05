from flask import make_response, jsonify, request, abort, redirect
from models import User
import json
import jwt
from datetime import datetime
from calendar import timegm

# access conig and logger using our data container
from libs.data_container import data_container as dc
# dc.logger.info('JWT...')

class JwtForRestApi(object):
	'''implement JWT token checks for my Flask REST API.'''

	def get_http_auth(self):
		''' read JWT token from HTTP Authorization header and verify and return payload.'''
		if 'Authorization' not in request.headers:
			return ({})
		
		auth_header = request.headers.get('Authorization')
		
		# get jwt token from header 'Bearer ##########TOKEN######'
		try:
			# fail on mailformed auth header
			token = auth_header.split(" ")[1]
		except:
			print ("DEBUG: auth_header: ", auth_header)
			result = {'error': 'token error', 'message': 'Malformed Authorization header.'}
			self.response(result, 401)
		
		try: 
			payload = Token.verify(token)
			# print("FOUND: Auth (payload):", payload)
			return payload
			
		except jwt.ExpiredSignatureError:
			result = {'error': 'token error', 'message': 'Token expired. Please log in again.'}
			self.response(result, 401)
		except jwt.InvalidTokenError as exc:
			result = {'error': 'token error', 'message': 'JWT Invalid Token {}'.format( exc.__class__.__name__) }
			self.response(result, 401)
		
		return({})

		
	def has_access(self, auth, method, model=None):		
		# auth : { uid:  , } (jwt payload)
		# method :  GET/PUT/POST/DELETE/PATCH
		# model : this item
		
		# print("DEBUG: has_access ",auth, method, model)
		if auth.get('admin', 'False') is True:
			# you are admin, all is fine!
			return()
			
		result = {'error': 'access denied', 'message': 'You are not admin. login, and get token with admin permisions.'}
		# print ("DEBUG: ", result)
		self.response(result, 401)
		
		
				
		

class Token(object):
	'''create and verify jwt tokens.'''
	
	secret = None

	# expire = 3600 * 12 # 12 hours
	expire = 3600

	#
	# dress up Token :
	#		
	@classmethod
	def _init_read_conig(cls):
		# read config settings from our config file, via our data_container singleton:

		# expire time, default 3600 seconds
		cls.expire = dc.config.get('jwt_token',{}).get('expire', 3600)
		# secret , default None
		cls.secret = dc.config.get('jwt_token',{}).get('secret', None)

		print("DEBUG: cls.secret: ", cls.secret)
		if cls.secret is None:
			dc.logger.info('JWT Token: auto-generating secret')
			import secrets 
			#only python > 3.6 , sorry config secret in your config.ini
			cls.secret = secrets.token_urlsafe(64)
			print("DEBUG: generating new cls.secret: ", cls.secret)

		
		dc.logger.debug("Token initialized ...")
		dc.logger.debug("Token.expire: {}".format(Token.expire))
		dc.logger.debug("Token.secret: {}".format(Token.secret))
		
	
	@staticmethod
	def create(user, admin=True, refresh=True, aud='default'):
		# payload
		p = {}
		#
		# “exp” (Expiration Time) Claim
		# “nbf” (Not Before Time) Claim
		# “iss” (Issuer) Claim
		# “aud” (Audience) Claim
		# “iat” (Issued At) Claim

		p['iat'] = timegm(datetime.utcnow().utctimetuple())
		p['nbf'] = p['iat'] - 1
		p['exp'] = p['iat'] + Token.expire
		
		# audience , single string, or array of strings
		p['aud'] = aud
	
		# user id
		p['uid'] = user.id
		
		# let's give everyone admin right
		p['admin'] = admin
		
		# token refresh permisions 
		p['refresh'] = refresh
		
		token = jwt.encode(p, Token.secret, algorithm='HS256').decode('utf-8')
		return(token)
		
	@staticmethod
	def verify(token, aud='default'):
		# audience , single string, or array of strings
		decoded = jwt.decode(token, Token.secret, audience=aud, algorithms=['HS256'])			
		
		# todo ... handle exception ?
		return(decoded)
	

# initialize token:
Token._init_read_conig()



#
# login and JWT 
#
# app.add_url_rule('/api/login', view_func=login_endpoint , methods=['POST'])
	
def login_endpoint():
	# dict we will return:
	result = {}

	# get POST data from HTTP request
	post_data = request.get_json()
	
	if post_data is None:
		result = {'status': False,'error': 'missing attributes', 'message': 'json data is missing.'}
		return(make_response(json.dumps(result, indent=4), 400, {'Content-Type': 'application/json'}))
		
	# post_data['email']
	# post_data['password']
	
	if 'email' not in post_data:
		result = {'status': False,'error': 'missing attribute', 'message': 'email field is missing in post data.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 400, {'Content-Type': 'application/json'}))
	
	if 'password' not in post_data:
		result = {'status': False,'error': 'missing attribute','message': 'password field is missing in post data.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 400, {'Content-Type': 'application/json'}))
		
	# get user from database
	u = User.where('email', post_data['email']).first()
	if not u:
		result = {'status': False,'error': 'access denied', 'message': 'User not found.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))

	# verify password
	if not u.do_verify_password(post_data['password']):
		result = {'status': False,'error': 'access denied', 'message': 'password incorrect.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))

	# is disabled
	if u.is_disabled:
		result = {'status': False,'error': 'access denied', 'message':'User disabled.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))
		
	# 
	# Password is verified and OK: make an JWT and return this
	# 
	
	token = Token.create(user = u)
	
	
	result = {'status': True, 'message':'User logged on.', 'token': token }
	# print ("DEBUG: json:", result)
	dc.logger.debug ("JWT login: user logged on: id {}, email {}".format( u.id, u.email))
	return(json.dumps(result, indent=4))
	
#
# login and JWT 
#
# app.add_url_rule('/api/refresh_token', view_func=token_refresh_endpoint , methods=['POST'])
def token_refresh_endpoint():
	# dict we will return:
	result = {}

	# Get token:
	if 'Authorization' not in request.headers:
		result = {'status': False,'error': 'access denied', 'message': 'no authorization header in http request.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))
	
	# get token from header 'Bearer ##########TOKEN######'
	token = request.headers.get('Authorization').split(" ")[1]
	
	try: 
		payload = Token.verify(token)
		# print("FOUND: Auth (payload):", payload)
	except jwt.ExpiredSignatureError:
		result = {'status': False,'error': 'token error', 'message': 'Token expired. Please log in again.'}
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))
	except jwt.InvalidTokenError as exc:
		result = {'status': False,'error': 'token error', 'message': 'JWT Invalid Token {}'.format( exc.__class__.__name__) }
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))

	# payload.uid : int
	# payload.refresh : True
	if not 'refresh' in payload:
		result = {'status': False,'error': 'access denied', 'message': 'Token has no permision to be refreshed.'}
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))

		
	# verify if user still has access.
	u = User.find(payload['uid'])
	if not u:
		result = {'status': False,'error': 'access denied', 'message': 'User not found. (uid not found)'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))

	# is disabled
	if u.is_disabled:
		result = {'status': False,'error': 'access denied', 'message':'User disabled.'}
		# print ("DEBUG: ", result)
		return(make_response(json.dumps(result, indent=4), 401, {'Content-Type': 'application/json'}))
		
	# 
	# all is verified and OK: make an JWT and return this
	# 
	
	token = Token.create(user = u)
	
	
	result = {'status': True, 'message':'User logged on.', 'token': token }
	# print ("DEBUG: json:", result)
	dc.logger.debug ("JWT refresh: user logged on: id {}, email {}".format( u.id, u.email))
	return(json.dumps(result, indent=4))
	