#!/bin/sh
: ${PYTHON:=python}
FAILED=0
export PYTHONPATH="${PYTHONPATH}:`realpath .`"
for file in tests/test_*.py ; do
	if ! ${PYTHON} $file ; then
		FAILED=1
	fi
done
if ! ${PYTHON} scripts/powerline-lint -p powerline/config_files ; then
	FAILED=1
fi
exit $FAILED
