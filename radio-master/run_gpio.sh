#!/usr/bin/env bash
pyex=`which python3`
sudo -E PULSE_SERVER=unix:/run/user/1000/pulse/native $pyex main.py
