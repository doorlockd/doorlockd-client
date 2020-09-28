#!/usr/bin/env python3

import sys
# support ctrl-c 
import signal

# flask webserver
from flask import Flask, jsonify, make_response, render_template
from flask_orator import Orator
#from waitress import serve -> moved into conditional statement to start waitress


# db models
from models import *

# global data_container
from libs.data_container import data_container as dc
# dc.config: config dict
# dc.logging: logging object
# dc.e: events object
# dc.hw: hardware dict

import toml
import logging

import client_api_local # client_api_local.ClientApiDoorlockd
dc.api = client_api_local.ClientApiDoorlockd()

# hardware:
from libs.Solenoid import Solenoid
from libs.Buzzer import Buzzer
from libs.Button import Button
from libs.Dummy import Dummy
from libs.RfidReaderRc522 import RfidReaderRc522, RfidActions
from libs.AutomatedActions import AutomatedActions, Delay1sec
from libs.UiLeds import UiLedsWrapper

# events
from libs.Events import Events
dc.e = Events()


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
# initilize hardware container
#
dc.hw = {}

# 
# UI Leds 
#
dc.hw['uileds'] = UiLedsWrapper() # will return the configured UiLeds Object


#
# Creating Flask application
#
app = Flask(__name__, static_url_path='', static_folder='static_html', template_folder='static_html')
app.debug = dc.config.get('webserver',{}).get('debug', False)
app.config['ORATOR_DATABASES'] = dc.config['ORATOR_DATABASES']

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
# handle CTRL-C / stop signal
#
def signal_handler_stop(signal, frame):
	dc.logger.info('stopping by sigint or sigterm (ctrl-c or systemd stop)')

	while dc.hw:
		# get item of hw list
		(hw_name, hw_obj) = dc.hw.popitem()
		
		# delete item from hw list, this will also call .__del__() 
		dc.logger.debug('exiting {}...'.format(hw_name))
		try:
			hw_obj.hw_exit()
		except AttributeError:
			pass

	dc.logger.info('exit after proper shutdown..')
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
	# our dummy hardware, can be used as placeholder for trigger_action.
	#
	dc.hw['dummy'] = Dummy()

	# 
	# Hardware: Solenoid
	#
	dc.hw['solenoid'] = Solenoid()
	rest_api_models.create_api_for_object(dc.hw['solenoid'], 'schema/schema.hw.solenoid.json', '/api/hw/solenoid', app)
	# subscribe to event open_door
	dc.e.subscribe('open_door', dc.hw['solenoid'].event_callback)

	# 
	# Hardware: Buzzer
	#
	dc.hw['buzzer'] = Buzzer()
	rest_api_models.create_api_for_object(dc.hw['buzzer'], 'schema/schema.hw.buzzer.json', '/api/hw/buzzer', app)
	# subscribe to event ring_buzzer
	dc.e.subscribe('ring_buzzer', dc.hw['buzzer'].event_callback) 


	# 
	# Hardware:  Button1, default functionality is intercom: trigger_action = open_door 
	#
	dc.hw['button1'] = Button('button1', trigger_action='open_door')
	rest_api_models.create_api_for_object(dc.hw['button1'], 'schema/schema.hw.button.json', '/api/hw/button1', app)

	# 
	# Hardware:  Button2, default functionality is doorbell: trigger_action = ring_buzzer 
	#
	dc.hw['button2'] = Button('button2', trigger_action='ring_buzzer')
	rest_api_models.create_api_for_object(dc.hw['button2'], 'schema/schema.hw.button.json', '/api/hw/button2', app)

	# Hardware:  Mifare RFID Reader  
	#
	dc.hw['rfidreader'] = RfidReaderRc522()
	rest_api_models.create_api_for_object(dc.hw['rfidreader'], 'schema/schema.hw.rfidreader.json', '/api/hw/rfidreader', app)
	# dc.hw['rfidreader'].start_thread()

	# register callback methods:
	dc.hw['rfidactions'] = RfidActions()
	dc.hw['rfidreader'].callback_tag_detected = dc.hw['rfidactions'].callback_tag_detected

	# Automated Actions:
	dc.hw['automated_actions'] = AutomatedActions()
	dc.hw['delay1sec'] = Delay1sec()
	rest_api_models.create_api_for_object(dc.hw['automated_actions'], 'schema/schema.hw.automated_actions.json', '/api/hw/automated_actions', app)
	

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
		
		

