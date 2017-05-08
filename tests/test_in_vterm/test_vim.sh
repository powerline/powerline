#!/bin/sh
. tests/shlib/common.sh
. tests/shlib/vterm.sh
. tests/shlib/vim.sh

enter_suite vim

VTERM_TEST_DIR="$ROOT/tests/vterm_vim"

vterm_setup "$VTERM_TEST_DIR"

test_vim() {
	if test "$PYTHON_IMPLEMENTATION" != CPython ; then
		# Can only link with cpython
		return 0
	fi
	if ! which "$POWERLINE_VIM_EXE" ; then
		return 0
	fi
	ln -sf "$(which "${POWERLINE_VIM_EXE}")" "$VTERM_TEST_DIR/path/vim"
	f="$ROOT/tests/test_in_vterm/test_vim.py"
	if ! "${PYTHON}" "$f" ; then
		local test_name="$(LANG=C "$POWERLINE_VIM_EXE" --cmd 'echo version' --cmd qa 2>&1)"
		fail "$test_name" F "Failed vterm test $f"
	fi
}

if test -z "$POWERLINE_VIM_EXE" && test -d "$ROOT/tests/bot-ci/deps/vim"
then
	for vim in "$OLD_VIM" "$NEW_VIM" ; do
		export POWERLINE_VIM_EXE="$vim"
		test_vim || true
	done
else
	export POWERLINE_VIM_EXE="${POWERLINE_VIM_EXE:-vim}"
	test_vim || true
fi

vterm_shutdown "$VTERM_TEST_DIR"

exit_suite
