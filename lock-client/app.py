#!/usr/bin/env python3

import sys

# support ctrl-c 
import os
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
	
	os.kill(os.getpid(), signal.SIGTERM)

dc.e.subscribe('abort_app', abort_app)




#
# Parse config modules:
#
# using importlib to dynamic load modules by name.
# config: ('nnn' = some unique name, 'xxx' = module file name)
# [module.nnn]
# type = "xxx"	
from libs.Module import ModuleManager

dc.module = ModuleManager()




#
# main loop
#
def main():
	
	if(dc.config.get('doorlockd',{}).get('enable_modules',True)):

		# initialize all modules 
		dc.module.load_all(dc.config.get('module', {}))

		# setup all loaded modules
		dc.module.do_all('setup')

		# enable all loaded modules
		dc.module.do_all('enable')

	print("doorlockd started.")
	# app_exit()


if __name__ == '__main__':
	main()
