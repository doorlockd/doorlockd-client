#!/usr/bin/env python

import sqlite3

#
# setup config
# 
import ConfigParser 
config = ConfigParser.ConfigParser()
config.read('config.ini')


#
# setup logging
# 
import logging
logger = logging.getLogger('doorlockd')


class KeyDB:
    '''interface to auth db in sqlitedb file'''

    def __init__(self):
        # path to sqlite file.
        self.db_file = config.get('auth_sqlite3', 'db_file')
        # SELECT statement to retrieve these 3 values (hwid,access,name) in the same order.
        self.sql_get = config.get('auth_sqlite3', 'sql_get')
        # INSERT statement to log unknown hwid 
        self.sql_insert = config.get('auth_sqlite3', 'sql_insert')
        
        logger.debug('{:s} auth_sqlite3 config: db_file {:s}.'.format(self.__class__.__name__, self.db_file ))
        logger.debug('{:s} auth_sqlite3 config: sql_get {:s}.'.format(self.__class__.__name__, self.sql_get ))
        logger.debug('{:s} auth_sqlite3 config: sql_insert {:s}.'.format(self.__class__.__name__, self.sql_insert ))
        
        self.open_db()
        
    def open_db(self):
        logger.info('{:s} open_db auth_sqlite3 using.'.format(self.__class__.__name__ ))
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def hwid2hexstr(self, uid):
        return(':'.join("{:02x}".format(p) for p in uid))
        
    
    def getent_by_hwid(self, hwid):
	hwid_str = self.hwid2hexstr(hwid)
	self.cursor.execute(self.sql_get, (hwid_str, ))
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
        self.cursor.execute(self.sql_insert, (hwid, ))
        self.conn.commit()

