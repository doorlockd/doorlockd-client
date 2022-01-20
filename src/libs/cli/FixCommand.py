from cleo import Command, Output

import sys
sys.path.append("..")

# import models , use connect_db to initialize the db
from models import *

def connect_db():
	# init db with correct config and env.
	from libs.data_container import data_container as dc
	dc.config_overwrite = {'doorlockd': {'enable_modules': False, 'enable_webserver': False,}}
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
		
		# init table
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
				
					try:
						# update db:
						tag.hwid = hwid_new
						done = str(tag.save())
						# self.line(done, verbosity=Output.VERBOSITY_VERBOSE)
						
					except Exception as e:
						done = "Failed: {}".format(repr(e))
						# self.line(done, verbosity=Output.VERBOSITY_VERBOSE)

					# display in table
					data.append([model, hwid_old, hwid_new, done])

		# result footer
		data.append(self.table_separator())
		data.append([self.table_cell('Found {} items'.format(len(data) -1 ), colspan=4)])
		
		# add data to table 
		table.set_rows(data)

		# render table
		table.render()
		
		

