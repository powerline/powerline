#!/bin/sh
. tests/common.sh

enter_suite lint

if ! ${PYTHON} scripts/powerline-lint -p powerline/config_files ; then
	fail "test" F "Running powerline-lint failed"
fi

exit_suite
