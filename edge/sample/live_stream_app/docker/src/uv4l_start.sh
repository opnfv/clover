#!/bin/bash

trap cleanup 2 3 15

cleanup()
{
   pkill uv4l
   exit 1
}

uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width $1 --height $2 --framerate $3 --server-option '--port=9090' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'

while true
do
   sleep 15
done
