#!/bin/sh
. tests/bot-ci/scripts/common/main.sh
set +x

FAILED=0

rm -rf tests/vterm
mkdir tests/vterm
mkdir tests/vterm/path

ln -s "$(which "${PYTHON}")" tests/vterm/path/python
ln -s "$(which bash)" tests/vterm/path
ln -s "$(which env)" tests/vterm/path
ln -s "$(which cut)" tests/vterm/path
ln -s "$PWD/scripts/powerline-render" tests/vterm/path
ln -s "$PWD/scripts/powerline-config" tests/vterm/path

cp -r tests/terminfo tests/vterm

FAIL_SUMMARY=""

test_tmux() {
	if test "$PYTHON_IMPLEMENTATION" = PyPy; then
		# FIXME PyPy3 segfaults for some reason, PyPy does it as well, but 
		# occasionally.
		return 0
	fi
	if ! which "${POWERLINE_TMUX_EXE}" ; then
		return 0
	fi
	ln -sf "$(which "${POWERLINE_TMUX_EXE}")" tests/vterm/path
	f=tests/test_in_vterm/test_tmux.py
	if ! "${PYTHON}" $f ; then
		echo "Failed vterm test $f"
		FAILED=1
		FAIL_SUMMARY="$FAIL_SUMMARY${NL}F $POWERLINE_TMUX_EXE $f"
	fi
}

if test -z "$POWERLINE_TMUX_EXE" && test -d tests/bot-ci/deps/tmux ; then
	for tmux in tests/bot-ci/deps/tmux/tmux-*/tmux ; do
		export POWERLINE_TMUX_EXE="$PWD/$tmux"
		test_tmux || true
	done
else
	export POWERLINE_TMUX_EXE="${POWERLINE_TMUX_EXE:-tmux}"
	test_tmux || true
fi

if test $FAILED -eq 0 ; then
	echo "$FAIL_SUMMARY"
	rm -rf tests/vterm
fi

exit $FAILED
