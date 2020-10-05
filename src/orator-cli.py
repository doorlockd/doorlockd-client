#!/usr/bin/env bpython -i 
#

from libs.data_container import data_container as dc
dc.config_overwrite = {'doorlockd': {'enable_hardware': False, 'enable_webserver': False,}}


from app import db

if __name__ == '__main__':
    db.cli.run()

else:
	print("db.cli.run() --> orator cli")
	print("create_user('root@localhost', 'secret')")
	print("passwd('root@localhost', 'secret')")

# 
# usage: 
# 
# bpython -i orator-cli.py 
#
##  
# create_user('root@localhost', 'secret')
##
# passwd('root@localhost', 'secret')
##


from models import *
def create_user(email, password_plain):
	User.create({'email': email, 'password_plain': password_plain})
	
	
def passwd(email, password_plain=None):
	# get user from database
	u = User.where('email', email).first_or_fail()
	
	# read password if needed
	if not password_plain:
		password_plain = input('new password: ') 
		
	# update password
	u.password_plain = password_plain
	
	# save changes
	u.save()
