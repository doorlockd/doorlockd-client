

install-systemd:
	install -m +x systemd.doorlockd.service /etc/systemd/system/doorlockd.service
	systemctl daemon-reload
	systemctl enable doorlockd
