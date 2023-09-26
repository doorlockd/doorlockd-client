#!/usr/bin/env python3

# pylint: disable=missing-docstring
import sys
from datetime import timedelta
# from gpiod import Chip , LineEvent#, line_request, line_event
import gpiod

import threading
import time

def event_detect(pin, edge=gpiod.LINE_REQ_EV_BOTH_EDGES, callback=lambda: print('Event detected')):
	# parse port name:
	(chip_name, line_number) = pin.split(' ', 1)

	# gpiod logic:
	chip = gpiod.Chip(chip_name)

	global gpiod_line
	gpiod_line = chip.get_line(int(line_number))		



	gpiod_line.request(consumer="button", type=edge)

	while True:
		if gpiod_line.event_wait(12):
			# event_read() is blocking function.
			event = gpiod_line.event_read()
			print ("DEBUG event: ", event)
			callback()
		else:
			print("timeout(1s)")
	
	

# MAIN:

# event_detect('gpiochip0 27')
t = threading.Thread(target=event_detect, args=['gpiochip0 27'])
t.start()

time.sleep(10)

print('DEBUG: gpiod_line.release()')
gpiod_line.release()

