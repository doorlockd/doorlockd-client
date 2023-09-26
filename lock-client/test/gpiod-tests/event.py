#!/usr/bin/env python3

# pylint: disable=missing-docstring
import sys
from datetime import timedelta
# from gpiod import Chip , LineEvent#, line_request, line_event
import gpiod

import threading
import time

class EventDetect:
	def __init__(self, bus, edge, callback):
		self.bus = bus
		self.edge = edge
		self.callback = callback
	
	def stop(self):
		'''remove myself from the event detect bus'''
		self.bus.remove(self.edge, self.callback)

class EventDetectBus:
	EDGE_RISING = 1
	EDGE_FALLING = 0
	EDGE_BOTH = 2

	def __init__(self, port):
		self.port = port
		
		# event bus
		self.bus_rising = [] 
		self.bus_falling = []
	
		# boolean to stop _run loop
		self.wait = None
		
		# thread
		self.thread = None

		# lock for adding/removeing events
		self.lock = threading.Lock()
	
	def add(self, edge, callback):
		start_thread = False
		
		with self.lock:
			# add event callback
			if edge == self.EDGE_RISING:
				self.bus_rising.append(callback)
			elif edge == self.EDGE_FALLING:
				self.bus_falling.append(callback)
			elif edge == self.EDGE_BOTH:
				# both
				self.bus_rising.append(callback)
				self.bus_falling.append(callback)
			else:
				raise ValueError("Unkown edge value.")
				return None
		
			# start thread (if needed)
			self._start()
			
		return EventDetect(self, edge, callback)	
			
				
				
	def remove(self, edge, callback):	
		with self.lock:
			# add event callback
			if edge == self.EDGE_RISING:
				self.bus_rising.remove(callback)
			elif edge == self.EDGE_FALLING:
				self.bus_falling.remove(callback)
			elif edge == self.EDGE_BOTH:
				# both
				self.bus_rising.remove(callback)
				self.bus_falling.remove(callback)
			else:
				raise ValueError("Unkown edge value.")

			# stop thread (if needed)
			if len(self.bus_rising) == 0 and len(self.bus_falling) == 0:
				# stop the loop 
				self.wait = False
		
			
	def _start(self):
		# enable the while loop
		self.wait = True
		
		# start thread when needed:
		if self.thread is None:
			# start _run in new thread:
			self.thread = threading.Thread(target=self._run)
			self.thread.start()
		

	def _run(self):

		# parse port name:
		(chip_name, line_number) = self.port.pin_name.split(' ', 1)

		# gpiod logic:
		self.chip = gpiod.Chip(chip_name)
		self.gpiod_line = self.chip.get_line(int(line_number))	
		self.gpiod_line.request(consumer="button", type=gpiod.LINE_REQ_EV_BOTH_EDGES)


		# run main detect loop 
		while self.wait:
			if self.gpiod_line.event_wait(2) and self.wait:
				event = self.gpiod_line.event_read()
				
				if event.type == gpiod.LineEvent.RISING_EDGE:
					 for callback in self.bus_rising:
						 callback()

				if event.type == gpiod.LineEvent.FALLING_EDGE:
					 for callback in self.bus_falling:
						 callback()
						 
				# call callback
				# print ("DEBUG: call callbacks ", self.port.pin_name, "event=", event)
			else:
				print("DEBUG: ", self.port.pin_name, "timeout(2s) ")

		print("DEBUG: ", self.port.pin_name, "event detect stoppped")		

		with self.lock:
			self.gpiod_line.release()

			# do we really need to stop?
			if self.wait is not True:
				self.thread = None		

			else:
				# aparently a new callback has been added while we got out of the loop, no worries we will restart ourselfs:
				self._run()

			
	def cleanup(self):
		with self.lock:
			# event bus
			self.bus_rising = [] 
			self.bus_falling = []
	
			# boolean to stop _run loop
			self.wait = False
		
						

class Port:
	def __init__(self, pin_name):
		self.pin_name = pin_name
		self.event = EventDetectBus(self)
		
		# parse port name:
		(chip_name, line_number) = self.pin_name.split(' ', 1)

		# gpiod logic:
		self.chip = gpiod.Chip(chip_name)
		
	def setup(self, type=gpiod.LINE_REQ_DIR_IN):
		# parse port name:
		(chip_name, line_number) = self.pin_name.split(' ', 1)

		# gpiod logic:
		self.gpiod_line = self.chip.get_line(int(line_number))	
		self.gpiod_line.request(consumer="button", type=type)
		
	def input(self):
		return self.gpiod_line.get_value()	


	def output(self, value):
		return self.gpiod_line.set_value(value)	

	def event_detect(self, edge, callback):
		return self.event.add(edge, callback)

	
	def cleanup(self):
		self.event.cleanup()

# # MAIN:
#
p1 = Port('gpiochip0 27') # IO	P8_17	gpiochip0 27	Button1
# # e1 = p1.event_detect(gpiod.LINE_REQ_EV_BOTH_EDGES, lambda: print('Rising Event detected'))
p1.setup()
e1_1 = p1.event_detect(EventDetectBus.EDGE_RISING, lambda: print('Button1 EDGE_RISING Event detected'))
e1_2 = p1.event_detect(EventDetectBus.EDGE_FALLING, lambda: print('Button1 EDGE_FALLING Event detected'))
#
print("p1:", p1, p1.input())
# p2 = Port('gpiochip2 1') # IO	P8_18	gpiochip2 1 	Button2
# e2 = p2.event_detect(0, lambda: print('Button2  Event1 detected'))
#
# time.sleep(3)
#
# print('DEBUG:e1_1 stop')
# e1_1.stop()
#
# time.sleep(1)
#
# print('DEBUG:e2 stop')
# e2.stop()
# e2 = p2.event_detect(0, lambda: print('Button2  Event2 detected'))
#
#
# time.sleep(2)
# print('DEBUG:e1_1 stop')
# e1_2.stop()
#
#
# time.sleep(10)
# p1.cleanup()
# p2.cleanup()