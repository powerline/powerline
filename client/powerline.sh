#!/bin/sh

fssock=y
test "${OSTYPE#darwin}" = "${OSTYPE}" && test "${OSTYPE#freebsd}" = "${OSTYPE}" && fssock=n

if test "$1" = "--socket" ; then
	shift
	ADDRESS="$1"
	shift
else
	ADDRESS="powerline-ipc-${UID:-`id -u`}"
	test "$fssock" = y && ADDRESS="/tmp/$ADDRESS"
fi

if test "$fssock" = y; then
	ENV=genv
else
	ENV=env
	ADDRESS="abstract-client:$ADDRESS"
fi

# Warning: env -0 does not work in busybox. Consider switching to parsing 
# `set` output in this case
(
	printf '%x\0' "$#"
	for argv in "$@" ; do
		printf '%s\0' "$argv"
	done
	printf '%s\0' "$PWD"
	$ENV -0
) | socat -lf/dev/null -t 10 - "$ADDRESS"

if test $? -ne 0 ; then
	powerline-render "$@"
fi
