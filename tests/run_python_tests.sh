#!/bin/sh
. tests/common.sh

enter_suite python

for file in tests/test_*.py ; do
	test_name="${file##*/test_}"
	if ! ${PYTHON} $file --verbose --catch ; then
		fail "${test_name%.py}" F "Failed test(s) from $file"
	fi
done

exit_suite
