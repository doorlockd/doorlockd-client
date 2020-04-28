#!/usr/bin/env python3

import sys
# support ctrl-c 
import signal

# flask webserver
from flask import Flask, jsonify, make_response
from flask_orator import Orator
#from waitress import serve -> moved into conditional statement to start waitress


# db models
from models import *

# global data_container
from libs.data_container import data_container as dc
# dc.config: config dict
# dc.logging: logging object

import toml
import logging

# hardware:
from libs.Solenoid import Solenoid
from libs.Buzzer import Buzzer
from libs.Button import Button
from libs.Dummy import Dummy


# Read Config settings 
try:
	dc.config = toml.load('config.ini')
except FileNotFoundError:
	sys.exit("Config file 'config.ini' is missing.")



#
# create logger with 'doorlockd'
#
logger = logging.getLogger('doorlockd')
logger.setLevel(dc.config.get('doorlockd',{}).get('log_level', 'NOTSET'))
# create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')

# console output on stderr
ch = logging.StreamHandler()
ch.setLevel(dc.config.get('doorlockd',{}).get('stderr_level', 'INFO'))
ch.setFormatter(formatter)
logger.addHandler(ch)

# file output
if dc.config.get('doorlockd',{}).get('logfile_name'):
	logger.info('logging to filename: {}, level: {}'.format(
		dc.config.get('doorlockd',{}).get('logfile_name'),
		dc.config.get('doorlockd',{}).get('logfile_level', 'INFO') ))

	fh = logging.FileHandler(dc.config.get('doorlockd',{}).get('logfile_name'))
	fh.setLevel(dc.config.get('doorlockd',{}).get('logfile_level', 'INFO'))
	fh.setFormatter(formatter)
	logger.addHandler(fh)

	
dc.logger = logger
dc.logger.info('doorlockd starting up...')


#
# Creating Flask application
#
app = Flask(__name__, static_url_path='', static_folder='static_html')
app.debug = dc.config.get('webserver',{}).get('debug', False)
app.config['ORATOR_DATABASES'] = dc.config['ORATOR_DATABASES']

#
# Initializing Orator, using flask app.config['ORATOR_DATABASES'] 
#
db = Orator(app)



#
# handle CTRL-C / stop signal
#
def signal_handler_stop(signal, frame):
	dc.logger.info('stopping by sigint or sigterm (ctrl-c or systemd stop)')

	while dc.hw:
		# get item of hw list
		item = dc.hw.pop()
		
		# delete item from hw list, this will also call .__del__() 
		dc.logger.debug('exiting {}...'.format(item))
		del dc.hw[item]

	dc.logger.info.info('raedy to exit')
	sys.exit(0)


def signal_handler_reload(signal, frame):
	dc.logger.info('SIG HUP received, nothing programmed to happen. ;-) ')


signal.signal(signal.SIGINT, signal_handler_stop)
signal.signal(signal.SIGTERM, signal_handler_stop)
signal.signal(signal.SIGHUP, signal_handler_reload)


#
# Main
#
if __name__ == '__main__':
	# enable flask api endpoints:
	import rest_api_models
	rest_api_models.add_to_flask(app)
	
	#
	# setup hardware
	#
	dc.hw = {}

	# 
	# our dummy hardware, can be used as placeholder for trigger_action.
	#
	dc.hw['dummy'] = Dummy()

	# 
	# Hardware: Solenoid
	#
	dc.hw['solenoid'] = Solenoid()
	# # any_object, json_schema, urlpath=None, app=None, methods=['GET', 'PUT']):
	# api_solenoid = rest_api_models.AnySingleObjectRestApi(hw_solenoid, 'schema/schema.hw.solenoid.json')
	# api_solenoid.flask_add_rules('/api/hw/solenoid', app, methods=['GET', 'PUT'])
	rest_api_models.create_api_for_object(dc.hw['solenoid'], 'schema/schema.hw.solenoid.json', '/api/hw/solenoid', app)

	# 
	# Hardware: Buzzer
	#
	dc.hw['buzzer'] = Buzzer()
	rest_api_models.create_api_for_object(dc.hw['buzzer'], 'schema/schema.hw.buzzer.json', '/api/hw/buzzer', app)


	# 
	# Hardware:  Button1, default functionality is intercom: trigger_action = solenoid 
	#
	dc.hw['button1'] = Button('button1', trigger_action='solenoid')
	rest_api_models.create_api_for_object(dc.hw['button1'], 'schema/schema.hw.button.json', '/api/hw/button1', app)

	# 
	# Hardware:  Button2, default functionality is doorbell: trigger_action = buzzer 
	#
	dc.hw['button2'] = Button('button2', trigger_action='buzzer')
	rest_api_models.create_api_for_object(dc.hw['button2'], 'schema/schema.hw.button.json', '/api/hw/button2', app)

	# 
	# Start Webserver 
	#
	if dc.config.get('webserver',{}).get('type', 'Flask').lower() == 'flask':
		#
		# Flask built in webserver , with DEBUG options
		#
		app.run(host=dc.config.get('webserver',{}).get('host', '0.0.0.0'), 
				port=dc.config.get('webserver',{}).get('port', 8000)) 
	elif dc.config.get('webserver',{}).get('type', 'Flask').lower() == 'waitress':
		#
		# Waitress webserver:
		#
		from waitress import serve
		
		serve(app, host=dc.config.get('webserver',{}).get('host', '0.0.0.0'), 
				   port=dc.config.get('webserver',{}).get('port', 8000)) 
		# fix waitress logging...
	else:
		dc.logger.error("Werbserver '{}' is not implemented, aborting.".format(dc.config.get('webserver',{}).get('type', 'Flask').lower()))
		sys.exit("Werbserver '{}' is not implemented, aborting.".format(dc.config.get('webserver',{}).get('type', 'Flask').lower()))
		
		

