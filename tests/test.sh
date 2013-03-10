#!/bin/sh
: ${PYTHON:=python}
if ${PYTHON} -c 'import sys; sys.exit(1 * (sys.version_info >= (2, 7)))' ; then
	# Python 2.6
	export PYTHONPATH="${PYTHONPATH}:`realpath .`"
	for file in tests/test_*.py ; do
		if ! ${PYTHON} $file ; then
			exit 1
		fi
	done
else
	${PYTHON} setup.py test
fi
