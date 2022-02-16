#!/bin/bash
cd /home/earth_elevation/src/earth_elevation
source venv/bin/activate
nohup python ee_server.py >/var/log/earth_elevation/earth_elevation.log 2>/var/log/earth_elevation/earth_elevation.err & disown
