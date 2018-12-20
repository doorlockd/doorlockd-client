#!/usr/bin/env python

import sqlite3

# path to sqlite file.
CONF_SQLITE_DB = '/opt/doorlockweb-beta/db.sqlite3'
# SELECT statement to retrieve these 3 values (hwid,access,name) in the same order.
CONF_SQLITE_GET = 'SELECT hwid,access,name FROM doorlock_tag WHERE hwid=?'
# INSERT statement to log unknown hwid 
CONF_SQLITE_INS = "INSERT INTO doorlock_unkowntag (hwid, create_date) VALUES (?,  datetime('now', 'localtime'))"



#
# setup logging
# 
import logging
logger = logging.getLogger('doorlockd')


class KeyDB:
    '''interface to auth db in sqlitedb file'''

    def __init__(self):
        self.open_db()
        
    def open_db(self):
        logger.debug('{:s} open_db sqlite3 using file {:s}.'.format(self.__class__.__name__, CONF_SQLITE_DB ))
	self.conn = sqlite3.connect(CONF_SQLITE_DB)
	self.cursor = self.conn.cursor()

    def hwid2hexstr(self, uid):
        return(':'.join("{:02x}".format(p) for p in uid))
        
    
    def getent_by_hwid(self, hwid):
	hwid_str = self.hwid2hexstr(hwid)
	self.cursor.execute(CONF_SQLITE_GET, (hwid_str, ))
	result = self.cursor.fetchone()

        if(result == None):
            # create "fail tag" with access=False
            tag = {'hwid':hwid_str, 'access': False, 'error': 'hwid not found in db'}
	
	    # Let's take care of adding unknown tag to db:
	    self.log_unknown_tag(hwid_str)

        else:
	    logger.debug( "sqlite3 KeyDB: match:" + str(result) )

            # we need a string True or False, not 1 or 2 
            if result[1] == 1:
                access = "True"
            else:
                access = "False"

            tag = {'hwid': result[0], 'access': access, 'name': result[2]}
        
        return (tag)


    def log_unknown_tag(self, hwid):
        self.cursor.execute(CONF_SQLITE_INS, (hwid, ))
        self.conn.commit()

