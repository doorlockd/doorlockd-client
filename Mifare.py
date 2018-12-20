#!/usr/bin/env python

import logging
logger = logging.getLogger('doorlockd')


from pirc522.rfid import RFID

class KeyReader:
    def __init__(self):
        # init RFID reader
        self.rdr = RFID(bus=1, device=0)
        logger.info('Myfare rfid KeyReader starting up...')

    def wait_for_key(self, callback):
        rdr = self.rdr
        rdr.wait_for_tag()
        (error, tag_type) = rdr.request()

        ## commmented out , to verbose...., perhaps no error here?.
	#if error:
        #   logger.debug("Can't detect RFID tag, rdr.request error")
            

        if not error:
            logger.debug("Tag detected")

            (error, uid) = rdr.anticoll()
            if not error:
                logger.debug("UID: " + str(uid))
                # Select Tag is required before Auth
                
                callback(uid)
                # if not rdr.select_tag(uid):
                # for sector in range(0, 63):
                #     rdr_dump_sector(rdr, sector, [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], uid)

                # Always stop crypto1 when done working
                #rdr.stop_crypto()

    def cleanup(self):
        '''calling rdr.stop_crypto() and rdr.cleanup() '''
        logger.debug('cleanup ' + self.__class__.__name__+ ': calling rdr.stop_crypto() and rdr.cleanup()')

        # Always stop crypto1 when done working
        self.rdr.stop_crypto()
        
        # Calls GPIO cleanup
        self.rdr.cleanup()

        
    def read_doorkey(self, hwid, tag_secret, sector ):
        ''' read doorkey from rfid tag by hwid, tag_secret, and sector id (1 ... 15)  '''
        if not rdr.select_tag(hwid):
            # Authenticate for sector (first block of sector)
            if not rdr.card_auth(rdr.auth_a, int(sector * 4 + 0 ), tag_secret, hwid):

                # calculate block number (first block of sector) 
                block = sector * 4 + 0
    
                # read block 
                (error, data) = rdr.read(block)
                

        # Always stop crypto1 when done working
        rdr.stop_crypto()

        return(error, data) 
        

        


