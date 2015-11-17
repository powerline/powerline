#!/bin/sh
FAILED=0
if ! sh tests/test_shells/test.sh --fast ; then
	echo "Failed shells"
	FAILED=1
fi
exit $FAILED
