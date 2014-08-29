#!/bin/sh
FAILED=0
for script in tests/*.vim ; do
	if ! vim -u NONE -S $script || test -f message.fail ; then
		echo "Failed script $script" >&2
		cat message.fail >&2
		rm message.fail
		FAILED=1
	fi
done
exit $FAILED
