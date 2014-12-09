#!/bin/sh
. tests/bot-ci/scripts/common/main.sh
FAILED=0

if test -z "$VIM" ; then
	if test "$PYTHON_IMPLEMENTATION" != "CPython" ; then
		exit 0
	fi
	NEW_VIM="$PWD/tests/bot-ci/deps/vim/tip-$PYTHON_VERSION/vim"
	OLD_VIM="$PWD/tests/bot-ci/deps/vim/v7-0-112-$PYTHON_VERSION/vim"
	if test -e "$OLD_VIM" ; then
		VIMS="NEW_VIM OLD_VIM"
	else
		VIMS="NEW_VIM"
	fi
else
	NEW_VIM="$VIM"
	OLD_VIM="$VIM"
fi

test_script() {
	local vim="$1"
	local script="$2"
	echo "Running script $script with $vim"
	if ! "$vim" -u NONE -S $script || test -f message.fail ; then
		echo "Failed script $script run with $VIM" >&2
		cat message.fail >&2
		rm message.fail
		FAILED=1
	fi
}

for script in tests/test_*.vim ; do
	if test "${script%.old.vim}" = "${script}" ; then
		test_script "$NEW_VIM" "$script"
	fi
done

if test -e "$OLD_VIM" ; then
	for script in tests/test_*.old.vim ; do
		test_script "$OLD_VIM" "$script"
	done
fi

exit $FAILED
