#!/bin/sh

use_filesystem=1
darwin=
if test -n "$OSTYPE" ; then
	# OSTYPE variable is a shell feature. supported by bash and zsh, but not 
	# dash, busybox or (m)ksh.
	if test "${OSTYPE#linux}" '!=' "${OSTYPE}" ; then
		use_filesystem=
	elif test "${OSTYPE#darwin}" ; then
		darwin=1
	fi
elif which uname >/dev/null ; then
	if uname -o | grep -iqF linux ; then
		use_filesystem=
	elif uname -o | grep -iqF darwin ; then
		darwin=1
	fi
fi

if test "$1" = "--socket" ; then
	shift
	ADDRESS="$1"
	shift
else
	ADDRESS="powerline-ipc-${UID:-`id -u`}"
	test -n "$use_filesystem" && ADDRESS="/tmp/$ADDRESS"
fi

if test -n "$darwin" ; then
	ENV=genv
else
	ENV=env
fi

if test -z "$use_filesystem" ; then
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
