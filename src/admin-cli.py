#!/usr/bin/env python3

from cleo import Application

# import Commands 
import libs.cli.UsersCommand as Users
import libs.cli.HelperCommand as Helper
import libs.cli.FixCommand as Fix

# init application
application = Application(complete=True)

# add commands to application
application.add(Users.CreateCommand())
application.add(Users.PasswdCommand())
application.add(Users.ListCommand())
application.add(Helper.GenSecretCommand())
# application.add(Fix.FixRemoveChecksumByteCommand())
Fix.addAllTo(application)

# run application
if __name__ == '__main__':
    application.run()
