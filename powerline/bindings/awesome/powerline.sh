#!/bin/sh

SLEEP=2
[[ "$1" != "" ]] && SLEEP="$1"

while true; do
	PL_AWESOME_RIGHT=$(powerline awesome right)
	echo "powerline_widget:set_markup('$PL_AWESOME_RIGHT')" | awesome-client
	sleep $SLEEP
done
