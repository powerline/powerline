#!/bin/bash
. tests/shlib/common.sh
. tests/shlib/vterm.sh

enter_suite vshells

vterm_setup

HAS_SOCAT=
HAS_C_CLIENT=

git init "$TEST_ROOT/3rd"
git --git-dir="$TEST_ROOT/3rd/.git" checkout -b BRANCH
export DIR1="[32m"
export DIR2=""
mkdir "$TEST_ROOT/3rd/$DIR1"
mkdir "$TEST_ROOT/3rd/$DIR2"
mkdir "$TEST_ROOT"/3rd/'\[\]'
mkdir "$TEST_ROOT"/3rd/'%%'
mkdir "$TEST_ROOT"/3rd/'#[bold]'
mkdir "$TEST_ROOT"/3rd/'(echo)'
mkdir "$TEST_ROOT"/3rd/'$(echo)'
mkdir "$TEST_ROOT"/3rd/'`echo`'
mkdir "$TEST_ROOT"/3rd/'«Unicode!»'
mkdir "$TEST_ROOT/fish_home"
mkdir "$TEST_ROOT/fish_home/fish"
mkdir "$TEST_ROOT/fish_home/fish/generated_completions"
cp -r "$ROOT/tests/test_shells/ipython_home" "$TEST_ROOT"

ln -s "$(command -v env)" "$TEST_ROOT/path"
ln -s "$(command -v git)" "$TEST_ROOT/path"
ln -s "$(command -v sleep)" "$TEST_ROOT/path"
ln -s "$(command -v cat)" "$TEST_ROOT/path"
ln -s "$(command -v false)" "$TEST_ROOT/path"
ln -s "$(command -v true)" "$TEST_ROOT/path"
ln -s "$(command -v kill)" "$TEST_ROOT/path"
ln -s "$(command -v echo)" "$TEST_ROOT/path"
ln -s "$(command -v which)" "$TEST_ROOT/path"
ln -s "$(command -v dirname)" "$TEST_ROOT/path"
ln -s "$(command -v wc)" "$TEST_ROOT/path"
ln -s "$(command -v stty)" "$TEST_ROOT/path"
ln -s "$(command -v cut)" "$TEST_ROOT/path"
ln -s "$(command -v bc)" "$TEST_ROOT/path"
ln -s "$(command -v expr)" "$TEST_ROOT/path"
ln -s "$(command -v mktemp)" "$TEST_ROOT/path"
ln -s "$(command -v grep)" "$TEST_ROOT/path"
ln -s "$(command -v sed)" "$TEST_ROOT/path"
ln -s "$(command -v rm)" "$TEST_ROOT/path"
ln -s "$(command -v tr)" "$TEST_ROOT/path"
ln -s "$(command -v uname)" "$TEST_ROOT/path"
ln -s "$(command -v test)" "$TEST_ROOT/path"
ln -s "$(command -v pwd)" "$TEST_ROOT/path"
ln -s "$(command -v hostname)" "$TEST_ROOT/path"
ln -s "$ROOT/tests/test_shells/bgscript.sh" "$TEST_ROOT/path"
ln -s "$ROOT/tests/test_shells/waitpid.sh" "$TEST_ROOT/path"

ln -s "$ROOT/scripts/powerline-config" "$TEST_ROOT/path"
ln -s "$ROOT/scripts/powerline-render" "$TEST_ROOT/path"
ln -s "$ROOT/client/powerline.py" "$TEST_ROOT/path"

if test -e "$ROOT/scripts/powerline" ; then
	ln -s "$ROOT/scripts/powerline" "$TEST_ROOT/path"
elif test -e client/powerline ; then
	ln -s "$ROOT/client/powerline" "$TEST_ROOT/path"
elif command -v powerline ; then
	ln -s "$(command -v powerline)" "$TEST_ROOT/path"
else
	echo "Executable powerline was not found"
	exit 1
fi

if test "$(
	file --mime-type --brief --dereference "$TEST_ROOT/path/powerline" \
	| cut -d/ -f1)" = "application" ; then
	HAS_C_CLIENT=1
fi

if command -v socat ; then
	HAS_SOCAT=1
	ln -s "$(command -v socat)" "$TEST_ROOT/path"
	ln -s "$ROOT/client/powerline.sh" "$TEST_ROOT/path"
fi

# Test type: daemon, renderer, …
# Test client: python, shell, c, none
# Test binding: *sh, ipython, pdb, …
test_shell() {
	local test_type="$1" ; shift
	local test_client="$1" ; shift
	local test_binding="$1" ; shift

	if test "$test_client" = shell && test -z "$HAS_SOCAT" ; then
		echo "Skipping test, socat not available"
		return
	fi
	if test "$test_client" = c && test -z "$HAS_C_CLIENT" ; then
		echo "Skipping test, C client not available"
		return
	fi
	if command -v "$test_binding" ; then
		ln -s "$(command -v "$test_binding")" "$TEST_ROOT/path"
	fi

	if ! "${PYTHON}" "$ROOT/tests/test_in_vterm/test_shells.py" \
		--type=$test_type \
		--client=$test_client \
		--binding=$test_binding \
		-- "$@"
	then
		local test_name="$test_type-$test_client-$test_binding"
		fail "$test_name" F "Failed vterm shell test"
	fi
}

test_shell renderer python dash -i || true

vterm_shutdown

exit_suite
