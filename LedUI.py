import pythonled

class LedUI:
	'''User Interface using the onboard led of beagleboneblack '''

	def __init__(self):
		self.led0 = pythonled.pythonled(0)
		self.led1 = pythonled.pythonled(1)
		self.led2 = pythonled.pythonled(2)
		self.led3 = pythonled.pythonled(3)

		self.led0.off()
		self.led1.off()
		self.led2.off()
		self.led3.off()

	def ui_ready(self):
		self.led0.times(100,2900)
		self.led1.times(100,2900)
		self.led2.times(100,2900)
		self.led3.times(100,2900)
		
	def ui_startup(self):
		self.led3.times(900,100)
		self.led2.times(900,100)
		self.led1.times(900,100)
		self.led0.times(900,100)
		
	def ui_shutdown(self):
		self.led0.times(900,100)
		self.led1.times(900,100)
		self.led2.times(900,100)
		self.led3.times(900,100)
	
	def cleanup(self):
		self.led0.heartbeat()
		self.led1.off()
		self.led2.off()
		self.led3.off()

	def ui_access_ok(self):
		self.led3.off()
		self.led2.off()
		self.led1.times(100,100)
		self.led0.off()
		

	def ui_access_fail(self):
		self.led0.off()
		self.led1.off()
		self.led2.off()
		self.led3.times(1100,100)


	
