#!/bin/sh
. tests/common.sh

enter_suite tmux

VTERM_TEST_DIR="$ROOT/tests/vterm_tmux"

rm -rf "$VTERM_TEST_DIR"
mkdir "$VTERM_TEST_DIR"
mkdir "$VTERM_TEST_DIR/path"

ln -s "$(which "${PYTHON}")" "$VTERM_TEST_DIR/path/python"
ln -s "$(which bash)" "$VTERM_TEST_DIR/path"
ln -s "$(which env)" "$VTERM_TEST_DIR/path"
ln -s "$(which cut)" "$VTERM_TEST_DIR/path"
ln -s "$ROOT/scripts/powerline-render" "$VTERM_TEST_DIR/path"
ln -s "$ROOT/scripts/powerline-config" "$VTERM_TEST_DIR/path"

cp -r "$ROOT/tests/terminfo" "$VTERM_TEST_DIR"

test_tmux() {
	if test "$PYTHON_IMPLEMENTATION" = PyPy; then
		# FIXME PyPy3 segfaults for some reason, PyPy does it as well, but 
		# occasionally.
		return 0
	fi
	if ! which "${POWERLINE_TMUX_EXE}" ; then
		return 0
	fi
	ln -sf "$(which "${POWERLINE_TMUX_EXE}")" "$VTERM_TEST_DIR/path"
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

if test $FAILED -eq 0 ; then
	rm -rf "$VTERM_TEST_DIR"
else
	echo "$FAIL_SUMMARY"
fi

exit_suite
