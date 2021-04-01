### To deploy on a new sensor
1. Image the micro SD card for 32-bit Raspbian
1. Copy the contents of this repository onto the sd card
1. Update sense/sense.yml for the sensor (update PG credentials and sensor values)
1. Update wpa_supplicant.conf to point to the right wifi network and credentials
1. Boot the pi, ssh into it and run sudo raspi-config in order to update the hostname, enable i2c, and change the root password
1. Run /home/pi/sense/configure.sh
