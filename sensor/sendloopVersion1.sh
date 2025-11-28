#!/usr/bin/env bash

while true
do
    sudo libcamera-jpeg -o image.jpg --width 640 --height 480
    python3 /home/zhao/sendtest.py
    sleep 5
done
