#!/bin/sh
FAILED=0
export PYTHON="${PYTHON:=python}"
export PYTHONPATH="${PYTHONPATH}:`realpath .`"
for script in tests/run_*_tests.sh ; do
	if ! sh $script ; then
		echo "Failed $script"
		FAILED=1
	fi
done
exit $FAILED
