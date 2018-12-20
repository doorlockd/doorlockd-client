# Doorlockd

### Connecting Mifare RC522 on first SPI.
First make sure SPIDEV is enabled on your Beaglebone black, add to `/boot/uEnv.txt` 
```
# for Debian 9.3 or newer ,  
dtb_overlay=/lib/firmware/BB-SPIDEV0-00A0.dtbo
# Note that when booting from SD, the u-boot from the EMMC is still used. so you need to flash the EMMC.
```

#### Install python module pi-rc522
I needed to use this workaround to install https://github.com/ondryaso/pi-rc522/issues/38


#### pinout 
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

| Solenoid | mode | BBB |
| --- | --- | --- |
| + | GPIO | P9_14 |
| - | GND | P9_02 |

