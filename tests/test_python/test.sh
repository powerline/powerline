#!/bin/sh
. tests/shlib/common.sh

enter_suite python final

for file in "$ROOT"/tests/test_python/test_*.py ; do
	test_name="${file##*/test_}"
	if ! "$PYTHON" "$file" --verbose --catch ; then
		fail "${test_name%.py}" F "Failed test(s) from $file"
	fi
done

exit_suite
