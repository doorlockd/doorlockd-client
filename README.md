# Doorlockd
RFID doorlock security access control system using PN532 and any linux supported single board computer.


## install

### clone files into /opt/doorlockd
	cd /opt && git clone https://github.com/wie-niet/doorlockd.git

### install python modules
	pip install -r requirements.txt

### install python libgpiod

	apt-get install python3-libgpiod

#### gpiod permisions fix
when needed set file permissions 

	sudo groupadd gpiod
	sudo usermod -G --append gpiod $USER

	sudo echo '# udev rules for gpio port access through libgpiod 
	SUBSYSTEM=="gpio", KERNEL=="gpiochip[0-4]", GROUP="gpiod", MODE="0660"' > /etc/udev/rules.d/60-gpiod.rules

### config.ini
Copy defaults form `config-default.ini` and save tham as `config.ini`.
In order to get a login token, use the `./login.py`, or simply configure the username + password in `config.ini`.


### install systemd.service

	install -m 644 systemd.doorlockd.service /etc/systemd/system/doorlockd.service
	systemctl daemon-reload
	systemctl enable brandmeldbot


	# or use git tracked file:
	# ln -s systemd.doorlockd.service /etc/systemd/system/doorlockd.service


## create admin user
Create, list or update admin user using admin-cli:

	# admin-cli.py users:create [-p|--password PASSWORD] [-c|--crypt CRYPT] [-d|--disabled] [--] <email>
	# admin-cli.py users:list
	# admin-cli.py users:passwd [-p|--password PASSWORD] [-c|--crypt CRYPT] [-d|--disable] [-e|--enable] [--] <email>


Best way to create a new user:

	./admin-cli.py users:create <your email address>	
And you will be prompted for a new password.


## Random secret for JWT
Generate secret for jwt_token config.

	./admin-cli.py gen:secret


## run
Enable debug mode to see what happens, run on commandline:

	./app.py
	

Or simply run deamon using systemctl:

	# restart doorlockd
	service doorlockd restart
	
	# read logfiles:
	journalctl --follow -u doorlockd
	
	