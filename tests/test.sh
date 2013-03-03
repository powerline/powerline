#!/bin/sh
if python -c 'import sys; sys.exit(1 * (sys.version_info >= (2, 7)))' ; then
	# Python 2.6
	export PYTHONPATH="${PYTHONPATH}:`realpath .`"
	for file in tests/test_*.py ; do
		if ! python $file ; then
			exit 1
		fi
	done
else
	python setup.py test
fi
