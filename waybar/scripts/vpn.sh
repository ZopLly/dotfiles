w#!/bin/bash

if tailscale status >/dev/null 2>&1; then
    echo "󰒘 VPN"
else
    echo "󰒙 OFF"
fi
