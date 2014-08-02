#!/bin/sh

ADDRESS="powerline-ipc-${UID:-`id -u`}"

# Warning: env -0 does not work in busybox. Consider switching to parsing 
# `set` output in this case
(
	for argv in "$@" ; do
		printf '%s\0' "$argv"
	done
	env -0 | sed 's/\(\x00\)\([^\x00]\)\|^/\1--env=\2/g'
	printf -- '--cwd=%s\0' "$PWD"
) | socat -lf/dev/null -t 10 - abstract-client:"$ADDRESS"

if test $? -ne 0 ; then
	powerline-render "$@"
fi
