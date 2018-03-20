#!/bin/bash

# start nginx server to handle incoming http requests
/usr/sbin/nginx &

# Process snort alerts
python grpc/snort_alerts.py

