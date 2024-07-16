#!/bin/bash

killall python3
source venv/bin/activate
nohup python3 -u zapier.py > out.log 2>&1 &
