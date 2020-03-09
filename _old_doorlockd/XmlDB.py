#!/usr/bin/env python

import xml.etree.ElementTree as ET



#
# setup logging
# 
import logging
logger = logging.getLogger('doorlockd')


class KeyDB:
    '''interface to auth db in xml file'''
    def __init__(self):
        self.read_db()
        
    def read_db(self):
        tree = ET.parse('keydb.xml')
        self.root = tree.getroot()

    def hwid2hexstr(self, uid):
        return(':'.join("{:02x}".format(p) for p in uid))
        
    
    def getent_by_hwid(self, hwid):
        # lookup key by hwid 
        hwid_str = self.hwid2hexstr(hwid)
        for key in self.root.findall("key[@hwid='{:s}']".format( hwid_str )):
            logger.debug( "KeyDB: match:" + str(key.attrib) )
            return key.attrib
    
        # return fail_key with access false .
        fail_key = {'hwid':hwid_str, 'access': False, 'error': 'hwid not found'}
        return fail_key
    
    
        

    