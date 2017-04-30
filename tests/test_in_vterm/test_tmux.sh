#!/bin/sh
. tests/shlib/common.sh
. tests/shlib/vterm.sh

enter_suite tmux

VTERM_TEST_DIR="$ROOT/tests/vterm_tmux"

vterm_setup "$VTERM_TEST_DIR"

ln -s "$(which env)" "$VTERM_TEST_DIR/path"
ln -s "$(which cut)" "$VTERM_TEST_DIR/path"
ln -s "$ROOT/scripts/powerline-render" "$VTERM_TEST_DIR/path"
ln -s "$ROOT/scripts/powerline-config" "$VTERM_TEST_DIR/path"

test_tmux() {
	if test "$PYTHON_IMPLEMENTATION" = PyPy; then
		# FIXME PyPy3 segfaults for some reason, PyPy does it as well, but 
		# occasionally.
		return 0
	fi
	if ! which "${POWERLINE_TMUX_EXE}" ; then
		return 0
	fi
	ln -sf "$(which "${POWERLINE_TMUX_EXE}")" "$VTERM_TEST_DIR/path/tmux"
	f="$ROOT/tests/test_in_vterm/test_tmux.py"
	if ! "${PYTHON}" "$f" ; then
		local test_name="$("$POWERLINE_TMUX_EXE" -V 2>&1 | cut -d' ' -f2)"
		fail "$test_name" F "Failed vterm test $f"
	fi
}

if test -z "$POWERLINE_TMUX_EXE" && test -d "$ROOT/tests/bot-ci/deps/tmux"
then
	for tmux in "$ROOT"/tests/bot-ci/deps/tmux/tmux-*/tmux ; do
		export POWERLINE_TMUX_EXE="$tmux"
		test_tmux || true
	done
else
	export POWERLINE_TMUX_EXE="${POWERLINE_TMUX_EXE:-tmux}"
	test_tmux || true
fi

vterm_shutdown "$VTERM_TEST_DIR"

exit_suite
