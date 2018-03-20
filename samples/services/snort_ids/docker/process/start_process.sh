#!/bin/bash

# Alert script processes snort alerts
./process/alert_process.sh &

# Main script to start grpc server that controls snort
./process/grpc_process.sh -D

