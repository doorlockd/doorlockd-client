#!/usr/bin/env python3

# pylint: disable=missing-docstring
import sys
from datetime import timedelta
# from gpiod import Chip , LineEvent#, line_request, line_event
import gpiod

import threading
import time
import signal

class Port:
	def __init__(self, pin_name):
		self.pin_name = pin_name
		
		# parse port name:
		(chip_name, line_number) = self.pin_name.split(' ', 1)

		# gpiod logic:
		self.chip = gpiod.Chip(chip_name)
		

	def event_detect(self, edge=gpiod.LINE_REQ_EV_BOTH_EDGES, callback=lambda: print('Event detected')):
		# parse port name:
		(chip_name, line_number) = self.pin_name.split(' ', 1)

		self.gpiod_line = self.chip.get_line(int(line_number))	
		self.gpiod_line.request(consumer="button", type=edge)
	
		while True:
			try:
				event = self.gpiod_line.event_read()
			except InterruptedError:
				print("debug InterruptedError")
				return
			print ("DEBUG event: ", event)
			callback()

			# if self.gpiod_line.event_wait(None):
			# 	# event_read() is blocking function.
			# 	event = self.gpiod_line.event_read()
			# 	print ("DEBUG event: ", event)
			# 	callback()
			# else:
			# 	print("timeout(1s)")
	
	

# MAIN:
print("start")

pin = Port('gpiochip0 27')

signal.signal(signal.SIGUSR1, lambda signum, frame: None)
t = threading.Thread(target=pin.event_detect)
t.start()

t2 = threading.Thread(target=pin.event_detect)
t2.start()

time.sleep(5)

print('DEBUG: gpiod_line.release()')
#pin.gpiod_line.release()
signal.pthread_kill(t.ident, signal.SIGUSR1)
print("A")
time.sleep(5)
print("B")



