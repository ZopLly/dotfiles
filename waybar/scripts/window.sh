#!/bin/bash

niri msg -j window | jq -r '
.[] |
	select(.is_focused == true |
	.app_id
'
