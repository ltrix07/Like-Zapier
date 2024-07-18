#!/bin/bash

killall python3
source /root/Like-Zapier/venv/bin/activate
nohup python3 -u /root/Like-Zapier/zapier.py > /root/Like-Zapier/out.log 2>&1 &
