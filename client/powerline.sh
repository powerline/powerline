#!/bin/sh

ADDRESS="powerline-ipc-${UID:-`id -u`}"

# Warning: env -0 does not work in busybox. Consider switching to parsing 
# `set` output in this case
(
	printf '%x\0' "$#"
	for argv in "$@" ; do
		printf '%s\0' "$argv"
	done
	printf '%s\0' "$PWD"
	env -0
) | socat -lf/dev/null -t 10 - abstract-client:"$ADDRESS"

if test $? -ne 0 ; then
	powerline-render "$@"
fi
