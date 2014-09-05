#!/bin/sh
FAILED=0
if ! sh tests/test_shells/test.sh --fast ; then
	echo "Failed shells"
	if ${PYTHON} -c 'import platform, sys; sys.exit(1 * (platform.python_implementation() == "PyPy"))' ; then
		FAILED=1
	fi
fi
exit $FAILED
