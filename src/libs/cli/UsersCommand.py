from cleo import Command

import sys
sys.path.append("..")

# import models , use connect_db to initialize the db
from models import *

def connect_db():
	# init db with correct config and env.
	from libs.data_container import data_container as dc
	dc.config_overwrite = {'doorlockd': {'enable_modules': False, 'enable_webserver': False,}}
	from app import db


class CreateCommand(Command):
	"""
	Create User

	users:create
		{email : create user , without -p|-c it will propmt for a password. }
		{--p|password= : set password }
		{--c|crypt= : set compatible crypt string }
		{--d|disabled : set disabled  }
	"""

	def handle(self):
		connect_db() # connect db
		
		email = self.argument('email')
		password = self.option('password')
		crypt = self.option('crypt')
		is_enabled = not self.option('disabled')

		if not password and not crypt:
			# get password from stdin
			password = self.secret('New password for {}: '.format(email))
			
		if password: 
			User.create({'email': email, 'password_plain': password, 'is_enabled': is_enabled})

		if crypt:
			User.create({'email': email, 'password_hash': crypt, 'is_enabled': is_enabled})
			
		self.line('changes saved to database')
		



class PasswdCommand(Command):
	"""
	Change Password or enable/disable an user.

	users:passwd
		{email : change password or enable|disable user, without -p,-c,-d,-e it will propmt for a password. }
		{--p|password= : set password }
		{--c|crypt= : set compatible crypt string }
		{--d|disable : disable user }
		{--e|enable : enable user }
	"""

	def handle(self):
		connect_db() # connect db
		
		email = self.argument('email')
		password = self.option('password')
		crypt = self.option('crypt')

		disable = self.option('disable')
		enable = self.option('enable')

		# you can't set both -d and -e 
		if disable and enable:
			self.line("You must choose, enable or disable, you can't do both!")
			return(False)

		# get user from database
		u = User.where('email', email).first_or_fail()
			
		# -e or -d is set:
		if disable or enable:
			u.is_enabled = bool(enable)
			self.line('set is_enabled = {}'.format(bool(enable)))
			

		# prompt for password if no options are set.
		if not password and not crypt and not (disable or enable):
			# get password from stdin
			password = self.secret('New password for {}: '.format(email))

		if password: 
			# update password
			u.password_plain = password
			self.line('new password set.')

		if crypt:
			# update password_hash
			u.password_hash = crypt
			self.line('password_hash is set.')
			
		u.save()
		self.line('changes saved to database')
		


class ListCommand(Command):
	"""
	List Users

	users:list
	"""

	def handle(self):
		connect_db() # connect db
		
		cols=['email', 'is_enabled', 'created_at', 'updated_at']
		
		table = self.table()
		table.set_headers(cols)		
		
		# list all created users
		data = []
		for u in User.all():
			row = []
			for col in cols:
				row.append(str(u.get_attribute(col)))
			data.append(row)
			
		table.set_rows(data)
		table.render()
		