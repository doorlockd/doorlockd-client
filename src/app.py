#!/usr/bin/env python3

import sys


# flask webserver
from flask import Flask, jsonify, make_response
from flask_orator import Orator

# db models
from models import *

# global data_container
from libs.data_container import data_container
# data_container.config: config dict
# data_container.logging: logging object

import toml
import logging



# Read Config settings 
try:
	data_container.config = toml.load('config.ini')
except FileNotFoundError:
	sys.exit("Config file 'config.ini' is missing.")



#
# create logger with 'doorlockd'
#
logger = logging.getLogger('doorlockd')
logger.setLevel(data_container.config.get('doorlockd',{}).get('log_level', 'NOTSET'))
# create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')

# console output on stderr
ch = logging.StreamHandler()
ch.setLevel(data_container.config.get('doorlockd',{}).get('stderr_level', 'INFO'))
ch.setFormatter(formatter)
logger.addHandler(ch)

# file output
if data_container.config.get('doorlockd',{}).get('logfile_name'):
	logger.info('logging to filename: {}, level: {}'.format(
		data_container.config.get('doorlockd',{}).get('logfile_name'),
		data_container.config.get('doorlockd',{}).get('logfile_level', 'INFO') ))

	fh = logging.FileHandler(data_container.config.get('doorlockd',{}).get('logfile_name'))
	fh.setLevel(data_container.config.get('doorlockd',{}).get('logfile_level', 'INFO'))
	fh.setFormatter(formatter)
	logger.addHandler(fh)

	
data_container.logger = logger
data_container.logger.info('doorlockd starting up...')


#
# Creating Flask application
#
app = Flask(__name__)
app.debug = True
app.config['ORATOR_DATABASES'] = data_container.config['ORATOR_DATABASES']

#
# Initializing Orator, using flask app.config['ORATOR_DATABASES'] 
#
db = Orator(app)

#
# ...
#



#
# Main
#
if __name__ == '__main__':
	# enable flask api endpoints:
	import rest_api_models
	rest_api_models.add_to_flask(app)
	
	app.run()

	
