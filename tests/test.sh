#!/bin/sh
: ${PYTHON:=python}
FAILED=0
export PYTHONPATH="${PYTHONPATH}:`realpath .`"
for file in tests/test_*.py ; do
	if ! ${PYTHON} $file --verbose --catch ; then
		echo "Failed test(s) from $file"
		FAILED=1
	fi
done
if ! ${PYTHON} scripts/powerline-lint -p powerline/config_files ; then
	echo "Failed powerline-lint"
	FAILED=1
fi
for script in tests/*.vim ; do
	if ! vim -u NONE -S $script || test -f message.fail ; then
		echo "Failed script $script" >&2
		cat message.fail >&2
		rm message.fail
		FAILED=1
	fi
done
if ! sh tests/test_shells/test.sh ; then
	echo "Failed shells"
	FAILED=1
fi
exit $FAILED
