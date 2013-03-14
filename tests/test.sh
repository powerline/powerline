#!/bin/sh
: ${PYTHON:=python}
FAILED=0
if ${PYTHON} -c 'import sys; sys.exit(1 * (sys.version_info >= (2, 7)))' ; then
	# Python 2.6
	export PYTHONPATH="${PYTHONPATH}:`realpath .`"
	for file in tests/test_*.py ; do
		if ! ${PYTHON} $file ; then
			exit 1
		fi
	done
else
	if ! ${PYTHON} setup.py test ; then
		FAILED=1
	fi
fi
if ! ${PYTHON} scripts/powerline-lint ; then
	FAILED=1
fi
exit $FAILED
