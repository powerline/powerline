#!/bin/sh
. tests/common.sh

enter_suite vterm

for t in tests/test_in_vterm/test_*.sh ; do
	test_name="${t##*/test_}"
	if ! sh "$t" ; then
		fail "${test_name%.sh}" F "Failed running $t"
	fi
done

exit_suite
