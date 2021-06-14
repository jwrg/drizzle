#!/bin/bash

# This shell script sets up a service on Raspbian for
# drizzle, sets up a redirect from port 8080 to port 80,
# and takes care of Python dependencies 

# Install spidev, RPi.GPIO and bjoern
sudo apt-get install libev-dev python2-dev python3-pip python3-flask
sudo pip3 install pi-plates
pip3 install spidev RPi.GPIO bjoern

# Set up iptables to redirect port 8080 to port 80
# NB this assumes interface wlan0
sudo iptables -A INPUT -i wlan0 -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -i wlan0 -p tcp --dport 8080 -j ACCEPT
sudo iptables -A PREROUTING -t nat -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 80
sudo iptables-save | sudo tee -a /etc/firewall.conf

# Copy the service file to /lib/systemd/system
sudo cp rpi/drizzle.service /lib/systemd/system/

# Set up permissions for the python script
chmod +x drizzle.py

# Set up permissions for the service file
sudo chmod 644 /lib/systemd/system/drizzle.service

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable drizzle.service
sudo systemctl start drizzle.service
