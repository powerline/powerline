#!/bin/sh
. tests/common.sh

enter_suite tmux

rm -rf tests/vterm_tmux
mkdir tests/vterm_tmux
mkdir tests/vterm_tmux/path

ln -s "$(which "${PYTHON}")" tests/vterm_tmux/path/python
ln -s "$(which bash)" tests/vterm_tmux/path
ln -s "$(which env)" tests/vterm_tmux/path
ln -s "$(which cut)" tests/vterm_tmux/path
ln -s "$PWD/scripts/powerline-render" tests/vterm_tmux/path
ln -s "$PWD/scripts/powerline-config" tests/vterm_tmux/path

cp -r tests/terminfo tests/vterm_tmux

test_tmux() {
	if test "$PYTHON_IMPLEMENTATION" = PyPy; then
		# FIXME PyPy3 segfaults for some reason, PyPy does it as well, but 
		# occasionally.
		return 0
	fi
	if ! which "${POWERLINE_TMUX_EXE}" ; then
		return 0
	fi
	ln -sf "$(which "${POWERLINE_TMUX_EXE}")" tests/vterm_tmux/path
	f=tests/test_in_vterm/test_tmux.py
	if ! "${PYTHON}" $f ; then
		local test_name="$("$POWERLINE_TMUX_EXE" -V 2>&1 | cut -d' ' -f2)"
		fail "$test_name" F "Failed vterm test $f"
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
	rm -rf tests/vterm_tmux
else
	echo "$FAIL_SUMMARY"
fi

exit_suite
