#!/bin/sh
. tests/shlib/common.sh

enter_suite lint final

if ! "$PYTHON" "$ROOT/scripts/powerline-lint" -p "$ROOT/powerline/config_files" ; then
	fail "test" F "Running powerline-lint failed"
fi

exit_suite
