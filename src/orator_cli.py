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
	print("list_users()")

# 
# usage: 
# 
# bpython -i orator_cli.py 
#
##  
# create_user('root@localhost', 'secret')
##
# passwd('root@localhost', 'secret')
##
# list_users()
##


from models import *
def create_user(email, password_plain, is_enabled=True):
	User.create({'email': email, 'password_plain': password_plain, 'is_enabled': is_enabled})
	
	
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

def list_users():
	# list all created users
	for u in User.all():
		print("{} email: {}".format('Enabled ' if u.is_enabled else 'Disabled', u.email))
		
		
# for importing keys:
def add_tag(hwid, description, is_disabled=False):
	if Tag.where('hwid', hwid).count() == 0:
		Tag.create({'hwid': hwid, 'description': description, 'is_disabled': is_disabled})
	else:
		print("Tag already exist.")
		

#
# upgrade scripts
# 
def upgrade_tags_v2():
	# read old table , convert data and insert into new table
	for t in db.table('pre_upgrade_tags_v2').select(db.raw('id, hwid, description, (NOT is_disabled) as is_enabled, created_at, updated_at')).get():
		print("insert:", t)
		db.table('tags').insert(t)
	
	# destroy old table
	db.table('tags').delete()



