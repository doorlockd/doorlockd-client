## install


### install python libgpiod

	apt-get install python3-libgpiod

### gpiod permisions fix
when needed set file permissions 

	sudo groupadd gpiod
	sudo usermod -G --append gpiod $USER

	sudo echo '# udev rules for gpio port access through libgpiod 
	SUBSYSTEM=="gpio", KERNEL=="gpiochip[0-4]", GROUP="gpiod", MODE="0660"' > /etc/udev/rules.d/60-gpiod.rules



