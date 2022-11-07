#!/bin/bash

# This shell script sets up a service on Raspbian for
# drizzle, sets up a redirect from port 8080 to port 80,
# and takes care of Python dependencies 

# This obviously doesn't work without sudo permissions

# This script also assumes the user doesn't know enough
# to set their own iptables rules, and sets up and saves
# a couple of rules to redirect HTTP requests to the app.
# Therefore, don't use this script if you think it will 
# nuke any rules you've set and saved

INTERFACE=wlan0
SRV_PORT=80
APP_PORT=8080

# Install spidev, RPi.GPIO and bjoern
sudo apt-get install libev-dev python2-dev python3-pip python3-flask iptables
sudo pip3 install pi-plates
pip3 install spidev RPi.GPIO bjoern

# Set up iptables to redirect HTTP port to application port
sudo iptables -A INPUT -i $INTERFACE -p tcp --dport $SRV_PORT -j ACCEPT
sudo iptables -A INPUT -i $INTERFACE -p tcp --dport $APP_PORT -j ACCEPT
sudo iptables -A PREROUTING -t nat -i $INTERFACE -p tcp --dport $SRV_PORT -j REDIRECT --to-port $APP_PORT
# Make the rules persistent
sudo iptables-save | sudo tee -a /etc/firewall.drizzle.conf
sudo echo "#!/bin/sh" | sudo tee -a /etc/network/if-pre-up.d/iptables
sudo echo "/sbin/iptables-restore < /etc/firewall.drizzle.conf" | sudo tee -a /etc/network/if-pre-up.d/iptables

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
