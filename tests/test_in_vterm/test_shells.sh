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

ln -s "$(which env)" "$TEST_ROOT/path"
ln -s "$(which git)" "$TEST_ROOT/path"
ln -s "$(which sleep)" "$TEST_ROOT/path"
ln -s "$(which cat)" "$TEST_ROOT/path"
ln -s "$(which false)" "$TEST_ROOT/path"
ln -s "$(which true)" "$TEST_ROOT/path"
ln -s "$(which kill)" "$TEST_ROOT/path"
ln -s "$(which echo)" "$TEST_ROOT/path"
ln -s "$(which which)" "$TEST_ROOT/path"
ln -s "$(which dirname)" "$TEST_ROOT/path"
ln -s "$(which wc)" "$TEST_ROOT/path"
ln -s "$(which stty)" "$TEST_ROOT/path"
ln -s "$(which cut)" "$TEST_ROOT/path"
ln -s "$(which bc)" "$TEST_ROOT/path"
ln -s "$(which expr)" "$TEST_ROOT/path"
ln -s "$(which mktemp)" "$TEST_ROOT/path"
ln -s "$(which grep)" "$TEST_ROOT/path"
ln -s "$(which sed)" "$TEST_ROOT/path"
ln -s "$(which rm)" "$TEST_ROOT/path"
ln -s "$(which tr)" "$TEST_ROOT/path"
ln -s "$(which uname)" "$TEST_ROOT/path"
ln -s "$(which test)" "$TEST_ROOT/path"
ln -s "$(which pwd)" "$TEST_ROOT/path"
ln -s "$(which hostname)" "$TEST_ROOT/path"
ln -s "$ROOT/tests/test_shells/bgscript.sh" "$TEST_ROOT/path"
ln -s "$ROOT/tests/test_shells/waitpid.sh" "$TEST_ROOT/path"

ln -s "$ROOT/scripts/powerline-config" "$TEST_ROOT/path"
ln -s "$ROOT/scripts/powerline-render" "$TEST_ROOT/path"
ln -s "$ROOT/client/powerline.py" "$TEST_ROOT/path"

if test -e "$ROOT/scripts/powerline" ; then
	ln -s "$ROOT/scripts/powerline" "$TEST_ROOT/path"
elif test -e client/powerline ; then
	ln -s "$ROOT/client/powerline" "$TEST_ROOT/path"
elif which powerline ; then
	ln -s "$(which powerline)" "$TEST_ROOT/path"
else
	echo "Executable powerline was not found"
	exit 1
fi

if test "$(
	file --mime-type --brief --dereference "$TEST_ROOT/path/powerline" \
	| cut -d/ -f1)" = "application" ; then
	HAS_C_CLIENT=1
fi

if which socat ; then
	HAS_SOCAT=1
	ln -s "$(which socat)" "$TEST_ROOT/path"
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
	if which "$test_binding" ; then
		ln -s "$(which "$test_binding")" "$TEST_ROOT/path"
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
