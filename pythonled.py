import os

class pythonled(object):
    """ class: pythonled
    
    Controls the LEDs on the beaglebone black.
    """

    def __init__(self,led):
        """init procedure
        
        initialise with the lednumber (0 to 3) on the beaglebone black

        :param led: lednumber
        """
        if (led >= 0 and led <=3):
            self.lednumber = led
        else:
            print 'This lednumber is not supported. Use 0, 1, 2 or 3'
            raise ValueError('Unsupported led numner.')

    def on(self):
        '''Switch the LED on
        by setting the trigger to 'none' and the brightness to 'high'. You need to set the trigger
        to 'none' first or else it would just brighten the LED and not make it static on''' 
        os.system('echo none > /sys/class/leds/beaglebone\:green\:usr%i/trigger' %(self.lednumber))
        os.system('echo 1 > /sys/class/leds/beaglebone\:green\:usr%i/brightness' %(self.lednumber))

    def off(self):
        '''Switch the LED off
        by setting the trigger to 'none' and the brightness to 'low'. You need to set the trigger
        to 'none' first or else it would just dimm the LED''' 
        os.system('echo none > /sys/class/leds/beaglebone\:green\:usr%i/trigger' %(self.lednumber))
        os.system('echo 0 > /sys/class/leds/beaglebone\:green\:usr%i/brightness' %(self.lednumber))

    def dimm(self):
        '''Set the brightness low
        Use ledOFF to switch off the LED'''
        os.system('echo 0 > /sys/class/leds/beaglebone\:green\:usr%i/brightness' %(self.lednumber))

    def bright(self):
        '''Set the brightness high
        Use ledON to switch on the LED'''
        os.system('echo 1 > /sys/class/leds/beaglebone\:green\:usr%i/brightness' %(self.lednumber))

    def heartbeat(self):
        '''Set the brightness high and pulse the LED with a heartbeat
        '''
        os.system('echo 1 > /sys/class/leds/beaglebone\:green\:usr%i/brightness' %(self.lednumber))
        os.system('echo heartbeat > /sys/class/leds/beaglebone\:green\:usr%i/trigger' %(self.lednumber))

    def times(self,on,off):
        '''Set the brightness high and pulse the LED with ON time and OFF time (ms).

        :param on: on time (ms)
        :param off: of time (ms)
        '''
        os.system('echo 1 > /sys/class/leds/beaglebone\:green\:usr%i/brightness' %(self.lednumber))
        os.system('echo timer > /sys/class/leds/beaglebone\:green\:usr%i/trigger' %(self.lednumber))
        os.system('echo %i > /sys/class/leds/beaglebone\:green\:usr%i/delay_on' %(on,self.lednumber))
        os.system('echo %i > /sys/class/leds/beaglebone\:green\:usr%i/delay_off' %(off,self.lednumber))

    def transient(self,state,timer):
        '''Set a timer
        Somehow the timerperiod (ms) is double what you would expect
        you can start in offstate or in onstate (0 or 1) and the stat is
        toggled after the timerperiod.
        
        :param state: the starting state [0 or 1]
        :param timer: time [ms]
         '''
        os.system('echo transient > /sys/class/leds/beaglebone\:green\:usr%i/trigger' %(self.lednumber))
        os.system('echo %i > /sys/class/leds/beaglebone\:green\:usr%i/state' %(state,self.lednumber))
        os.system('echo %d > /sys/class/leds/beaglebone\:green\:usr%i/duration' %(timer,self.lednumber))
        os.system('echo 1 > /sys/class/leds/beaglebone\:green\:usr%i/activate' %(self.lednumber))

def mainfunction():
    """A mainfunction as an example
    """
    user0 = pythonled(0)
    user0.on()
    user1 = pythonled(1)
    user1.heartbeat()
    user2 = pythonled(2)
    user2.times(250,100)
    user3 = pythonled(3)
    user3.transient(0,1000)

    user0.off()
    user1.off()
    #user2.off()
    user3.off()


if __name__ == '__main__':
    mainfunction()
