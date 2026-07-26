#!/bin/bash

niri msg focused-window | grep "Title" | sed 's/.*://'
