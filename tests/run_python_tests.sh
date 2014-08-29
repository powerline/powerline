#!/bin/sh
FAILED=0
for file in tests/test_*.py ; do
	if ! ${PYTHON} $file --verbose --catch ; then
		echo "Failed test(s) from $file"
		FAILED=1
	fi
done
exit $FAILED
