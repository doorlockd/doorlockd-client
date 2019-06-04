install: install-systemd install-logrotate

install-systemd:
	install -m +x systemd.doorlockd.service /etc/systemd/system/doorlockd.service
	systemctl daemon-reload
	systemctl enable doorlockd
	
install-logrotate:
	install -m 644 logrotate.d.doorlockd /etc/logrotate.d/doorlockd
