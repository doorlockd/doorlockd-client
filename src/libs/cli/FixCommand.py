from cleo import Command

import sys
sys.path.append("..")

# import models , use connect_db to initialize the db
from models import *

def connect_db():
	# init db with correct config and env.
	from libs.data_container import data_container as dc
	dc.config_overwrite = {'doorlockd': {'enable_hardware': False, 'enable_webserver': False,}}
	from app import db


def addAllTo(application):
	"""
	add all commands in here to application
	"""
	application.add(FixRemoveChecksumByteCommand())
	
	

class FixRemoveChecksumByteCommand(Command):
	"""
	Remove all hwid checksum bytes in db, for all *Tag like models (hwid "01:02:03:04:05" -> "01:02:03:04")

	fix:remove_checksum_byte 
	"""

	def handle(self):
		connect_db() # connect db
		
		cols=['model','hwid old', 'hwid new', 'done']
		
		table = self.table()
		table.set_headers(cols)		
		
		data = []

		# all 'Tag' like models with .hwid attributes
		for model in ['Tag', 'UnknownTag']:
			# for all items 
			for tag in globals()[model].all():
				hwid_old = tag.hwid
			
				# is hwid 5 bytes ("01:02:03:04:05")
				if(len(hwid_old) == 14 ):
					# remove checksum byte
					hwid_new = hwid_old[0:11] # first 11 chars
				
					# update db:
					tag.hwid = hwid_new
					done = tag.save()

					# display in table
					data.append([model, hwid_old, hwid_new, str(done)])
			
		table.set_rows(data)
		table.render()
		

		


