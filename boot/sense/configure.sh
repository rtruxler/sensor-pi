#!/usr/bin/env bash

# exit if an error occurs
set -e

sudo apt-get update
sudo apt-get install -y python3-smbus vim libpq5 libgpiod2
sudo pip3 install adafruit-circuitpython-busdevice
sudo pip3 install adafruit-circuitpython-ads1x15
sudo pip3 install psycopg2
sudo pip3 install Adafruit_DHT
sudo pip3 install pyyaml

echo "Updating rc.local"
sudo sed 's/exit 0//g' /etc/rc.local > ./rc.local
echo "sudo python3 /home/pi/sense/sense.py &" >> ./rc.local
echo "exit 0" >> ./rc.local
sudo cp ./rc.local /etc/rc.local

echo "Rebooting"
sleep 3
sudo reboot
