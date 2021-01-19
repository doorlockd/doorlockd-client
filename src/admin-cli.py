#!/usr/bin/env python3

from cleo import Application

# import Commands 
import libs.cli.UsersCommand as Users
import libs.cli.HelperCommand as Helper

# init application
application = Application()

# add commands to application
application.add(Users.CreateCommand())
application.add(Users.PasswdCommand())
application.add(Users.ListCommand())
application.add(Helper.GenSecretCommand())

# run application
if __name__ == '__main__':
    application.run()
