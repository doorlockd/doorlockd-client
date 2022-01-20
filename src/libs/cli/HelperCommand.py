from cleo import Command

# import sys
# sys.path.append("..")
#
# from libs.data_container import data_container as dc
# dc.config_overwrite = {'doorlockd': {'enable_modules': False, 'enable_webserver': False,}}
#
# from app import db
# from models import *




class GenSecretCommand(Command):
	"""
	Generate secret for jwt_token config.

	gen:secret  : Generate secret for jwt_token config.
	"""

	def handle(self):
		
		import secrets 
		#only python > 3.6 , sorry config secret in your config.ini
		secret = secrets.token_urlsafe(64)
		
		self.line('# ')
		self.line('# Add the information below the [jwt_token] section in your config.ini:')
		self.line('# ')
		self.line('[jwt_token]')
		self.line('secret = "{}"'.format(secret))
		self.line(' ')
		

