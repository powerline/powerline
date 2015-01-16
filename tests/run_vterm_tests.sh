#!/bin/sh
set -e
FAILED=0
if ! sh tests/test_in_vterm/test.sh ; then
	echo "Failed vterm"
	FAILED=1
fi
exit $FAILED
