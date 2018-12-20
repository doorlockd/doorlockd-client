
install:
	git checkout-index  -a -f --prefix=/opt/doorlock/

install-systemd:
	install -m +x systemd.doorlockd.service /etc/systemd/system/doorlockd.service
