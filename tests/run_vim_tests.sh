#!/bin/sh
. tests/bot-ci/scripts/common/main.sh
VIM=$PWD/tests/bot-ci/deps/vim/tip-$PYTHON_VERSION/vim
FAILED=0
for script in tests/test_*.vim ; do
	if ! $VIM -u NONE -S $script || test -f message.fail ; then
		echo "Failed script $script run with $VIM" >&2
		cat message.fail >&2
		rm message.fail
		FAILED=1
	fi
done
exit $FAILED
