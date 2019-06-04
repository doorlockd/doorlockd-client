

install-systemd:
	install -m +x systemd.doorlockd.service /etc/systemd/system/doorlockd.service
	systemctl daemon-reload
	systemctl enable doorlockd
	install -m logrotate.d.doorlockd /etc/logrotate.d/doorlockd
