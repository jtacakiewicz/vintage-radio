#!/usr/bin/env bash
pyex=`which python`
sudo -E PULSE_SERVER=unix:/run/user/1000/pulse/native $pyex main.py
