# Drizzle
Pi-plates and Flask to make it rain.

## Overview
This is a small Flask web app for controlling relays in
conjunction with a
[Pi-Plates RELAYplate](https://pi-plates.com/product/relayplate/).
Relays are mapped to an index which can be used to
activate and de-activate relays, and set timers for
relays.

It is intended for home use only and is provided with
NO WARRANTY.  USE AT YOUR OWN RISK.
That having been said, please use.

## Installation
Clone this repo, then run setup.sh or just read it to get
the gist of what you need to do to get wet.

## Configuration
Just read the code and set some constants in config.json;
it's not a big codebase nor is there a lot for the user to
set.  A blueprint for setting config values via GUI is
forthcoming.

To change how the app displays, edit the stylesheet and
the templates.  Or don't, it's up to you.

## Usage
When on the same network as the RPi, point your phone at
its address (on port 80) to turn sprinkler zones on and
off.

Alternatively, you can skip the browser part and send HTTP
requests directly to the app to turn zones and timers on
and off.  One could use this for cron jobs using curl, for
example, to periodically turn on/off relays.
