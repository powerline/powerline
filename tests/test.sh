#!/bin/bash
. tests/bot-ci/scripts/common/main.sh

FAILED=0

if test -n "$USE_UCS2_PYTHON" ; then
	export LD_LIBRARY_PATH=/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib
	set +e
	. virtualenvwrapper.sh
	workon cpython-ucs2-$UCS2_PYTHON_VARIANT
	set -e
fi

export PYTHON="${PYTHON:=python}"
export PYTHONPATH="${PYTHONPATH}:`realpath .`"
for script in tests/run_*_tests.sh ; do
	if ! sh $script ; then
		echo "Failed $script"
		FAILED=1
	fi
done
exit $FAILED
