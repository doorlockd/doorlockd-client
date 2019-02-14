# Doorlockd

## install software 
### Download
Choose your favorite option to download:
1. Download and extract zip into `/opt/doorlockd`
2. Use git `cd /opt/ && git clone https://github.com/wie-niet/doorlockd.git`

The software and configuration files are now located in `/opt/doorlockd`

### Configure
Copy `config.example.ini` to `config.ini` and edit.


## Mifare RC522 on first SPI.
First make sure SPIDEV is enabled on your Beaglebone black, add to `/boot/uEnv.txt` 
```
# for Debian 9.3 or newer ,  
dtb_overlay=/lib/firmware/BB-SPIDEV0-00A0.dtbo
# Note that when booting from SD, the u-boot from the EMMC is still used. so you need to flash the EMMC.
```

#### Install python module pi-rc522
I needed to use this workaround to install https://github.com/ondryaso/pi-rc522/issues/38


#### pinout RC522 on first SPI Beaglebone Black
| RC522 | mode | BBB |
| --- | --- | --- |
| 1 | SDA | P9_17 |
| 2 | SCK | P9_22 |
| 3 | MOSI | P9_18 |
| 4 | MISO | P9_21 |
| 5 | IRQ | P9_15 |
| 6 | GND | P9_01 |
| 7 | RST | P9_23 |
| 8 | 3.3V | P9_03 |


## Solenoid

Use the GPIO ports as set in your config.ini

| Solenoid | mode | BBB |
| --- | --- | --- |
| + | GPIO | P9_14 |
| - | GND | P9_02 |


### Circuit
I've used this circuit to gain enough power to work the solenoid.
```

   12 V +------------------------------+-->  Solenoid +
                                       |
+-------+                    2+--+-|>|-+
|       |      +----+   1 .--/   |  D1
|  GPIO +---+--+ R1 +----(->| )	 |
|       |   |  +----+     `--\   +-------->  Solenoid -
|       |  +++           T1  3+
|       |  |R|                |
|       |  |2|                |
|       |  +++                |
|       |   |                 |
|       | --+--               |
|       |  \ /  =>            |
|       |   V  LED1           |
|       | --+--               |
|   GND +---+-----------------+
|       |                     |
+-------+                     |
                              |
 12V GND ---------------------+
```
```
R1: 2k2 Ω
R2: 100 Ω
T1: generic n channel fet (example STU60N3LH5)   
D1: generic diode (example. 1N4007)
LED1: red LED
```

## Button

| Button | mode | BBB |
| --- | --- | --- |
| + | GPIO | P8_12 |
| - | GND | P8_02 |

### circuit
It's advisable to add an extra resistor to GPIO port, this is to prevent any damage on software failure when this gpio port would accidently be used as output and set to high.
```
+------+
|      |  +----+
| GPIO +--+ R1 +---+
|      |  +----+   |
|      |           \  
|      |            \  <- Switch
|      |           |
| GND  +-----------+
|      |
+------+
```
```
R1:  not more than internal PUD_UP resistor and not to low short circuit when this output is set to high.
```

## Start at boot
use `sudo make install-systemd` to install and enable the systemd service.  After that you can use `sudo service doorlockd [start|stop|status]` to start or stop the proces.

