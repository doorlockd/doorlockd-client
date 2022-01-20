#!/usr/bin/env python3

import sys
# support ctrl-c 
import signal

# global data_container
from libs.data_container import data_container as dc
# dc.config: config dict
# dc.module: 
dc.io_port = {} # dc.io_port
# ?dc.logging: logging object
# ?dc.e: events object
# ?dc.hw: hardware dict

import toml
import logging

	
#
# exit
#

dc.exit_value = 0 # set exit value

def app_exit():
	dc.logger.info('start exit')

	if hasattr(dc, 'module'):
		# setup all loaded modules
		# dc.module.disable_all()
		dc.module.do_all('disable')		
	
		# enable all loaded modules
		# dc.module.teardown_all()
		dc.module.do_all('teardown')		

	dc.logger.info('exit after proper shutdown.. (Exit value={})'.format(dc.exit_value))
	# sys.exit(0)
	sys.exit(dc.exit_value)


signal.signal(signal.SIGINT, lambda signal, frame: app_exit())
signal.signal(signal.SIGTERM, lambda signal, frame: app_exit())



# Read Config settings 
try:
	dc.config = toml.load('config.ini')
		
except FileNotFoundError:
	sys.exit("Config file 'config.ini' is missing.")
	
# overwrite config (can for example be set when imported from an cli script)
if(hasattr( dc, 'config_overwrite')):	
	for section in dc.config_overwrite.keys():
		
		# add section when missing
		if dc.config.get(section,False):
			dc.config[section] = {}
		
		for key, value in dc.config_overwrite[section].items():
			print("overwrite config: ['{}'] {} = ".format(section, key), value)
			dc.config[section][key] = value
			



#
# create logger with 'doorlockd'
#
logger = logging.getLogger()
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
# events
#
from libs.Events import Events
dc.e = Events()



# add abort event
def abort_app(data):
	dc.exit_value = 1
	
	# hackish but it works
	dc.logger.info('sending abort signal SIGTERM to self. (Exit value={})'.format(dc.exit_value))
	
	import os
	import signal
	os.kill(os.getpid(), signal.SIGTERM)

dc.e.subscribe('abort_app', abort_app)



#
# Auth db
#


# db models
from models import *


# if(dc.config.get('doorlockd',{}).get('enable_webserver',True)):
# flask webserver
from flask import Flask, jsonify, make_response, render_template
#from waitress import serve -> moved into conditional statement to start waitress
from flask_orator import Orator

#
# Creating Flask application
#
app = Flask(__name__, static_url_path='', static_folder='static_html', template_folder='static_html')
app.debug = dc.config.get('webserver',{}).get('debug', False)
app.config['ORATOR_DATABASES'] = dc.config['ORATOR_DATABASES']

# add to datacontainer:
dc.flask_app = app

@app.route("/")
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('index.html'), 404


# config webserver: enable_cors = False|True
if dc.config.get('webserver',{}).get('enable_cors', False):
	from flask_cors import CORS
	CORS(app) # This will enable CORS for all routes
	# Set CORS options on app configuration
	app.config['CORS_HEADERS'] = "Content-Type"
	app.config['CORS_RESOURCES'] = {r"/api/*": {"origins": ['http://localhost:4200','http://localhost','*']}}

	dc.logger.warning('Warning: CORS enabled on api server.')
	

#
# Initializing Orator, using flask app.config['ORATOR_DATABASES'] 
#
db = Orator(app)

#
# auth/lookup rfid tags:
from libs.rfid_auth import RfidAuth
dc.rfid_auth = RfidAuth()

#
# Main Webserver
#
if(dc.config.get('doorlockd',{}).get('enable_webserver',True)): 
	# enable flask api endpoints:
	import rest_api_models
	rest_api_models.add_to_flask(app)

	#
	# #
	# # setup hw endpoints
	# #
	# if(dc.config.get('doorlockd',{}).get('enable_hardware',True)):
	# 	rest_api_models.create_api_for_object(dc.hw['solenoid'], 'schema/schema.hw.solenoid.json', '/api/hw/solenoid', app)
	# 	rest_api_models.create_api_for_object(dc.hw['buzzer'], 'schema/schema.hw.buzzer.json', '/api/hw/buzzer', app)
	#
	# 	# buttons:
	# 	for button in dc.hw['buttons']:
	# 		rest_api_models.create_api_for_object(button, 'schema/schema.hw.button.json', '/api/hw/{}'.format(button.config_name), app)
	#
	# 	# rest_api_models.create_api_for_object(dc.hw['button2'], 'schema/schema.hw.button.json', '/api/hw/button2', app)
	# 	rest_api_models.create_api_for_object(dc.hw['rfidreader'], 'schema/schema.hw.rfidreader.json', '/api/hw/rfidreader', app)
	# 	rest_api_models.create_api_for_object(dc.hw['automated_actions'], 'schema/schema.hw.automated_actions.json', '/api/hw/automated_actions', app)
	#




#
# Parse config modules:
#
# using importlib to dynamic load modules by name.
# config: ('nnn' = some unique name, 'xxx' = module file name)
# [module.nnn]
# type = "xxx"	
from libs.Module import ModuleManager

dc.module = ModuleManager()

if(dc.config.get('doorlockd',{}).get('enable_modules',True)):
	
	# initialize all modules 
	dc.module.load_all(dc.config.get('module', {}))

	# setup all loaded modules
	dc.module.do_all('setup')		

	# enable all loaded modules
	dc.module.do_all('enable')		
	


# 
# Start Webserver 
#
if(dc.config.get('doorlockd',{}).get('enable_webserver',True)): 
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
	
	

#
# main loop
#


print("doorlockd started.")

# app_exit()

