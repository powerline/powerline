: ${USER:=`id -un`}
: ${HOME:=`getent passwd $USER | cut -d: -f6`}

if test -z "${PYTHON}" ; then
	if test -n "$USE_UCS2_PYTHON" ; then
		LD_LIBRARY_PATH="$HOME/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib${LD_LIBRARY_PATH:+:}${LD_LIBRARY_PATH}"
	fi
fi

export LD_LIBRARY_PATH
export USER
export HOME

if test -n "$USE_UCS2_PYTHON" ; then
	POWERLINE_VIRTUALENV="cpython-ucs2-$UCS2_PYTHON_VARIANT"
	PYTHON="$HOME/.virtualenvs/$POWERLINE_VIRTUALENV/bin/python"
	if test -n "$BASH_VERSION" ; then
		set +e
		. virtualenvwrapper.sh
		workon "$POWERLINE_VIRTUALENV"
		set -e
	fi
fi

. tests/bot-ci/scripts/common/main.sh silent

export USER HOME

if test -z "$FAILED" ; then
	FAILED=0

	FAIL_SUMMARY=""

	TMP_ROOT="$ROOT/tests/tmp"
	export FAILURES_FILE="$ROOT/tests/status"
fi

ANSI_CLEAR="\033[0K"

travis_fold() {
	local action="$1"
	local name="$2"
	name="$(echo -n "$name" | tr '\n\0' '--' | sed -r 's/[^A-Za-z0-9]+/-/g')"
	name="$(echo -n "$name" | sed -r 's/-$//')"
	echo -en "travis_fold:${action}:${name}\r${ANSI_CLEAR}"
}

print_environ() {
	echo "Using $PYTHON_IMPLEMENTATION version $PYTHON_VERSION."
	echo "Path to Python executable: $PYTHON."
	echo "Root: $ROOT."
	echo "Branch: $BRANCH_NAME."
	echo "sys.path:"
	"$PYTHON" -c "for path in __import__('sys').path: print('  %r' % path)"
}

enter_suite() {
	set +x
	local suite_name="$1" ; shift
	local final="$1"
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE}/$suite_name"
	travis_fold start "$POWERLINE_CURRENT_SUITE"
	print_environ
	if test "$final" = final ; then
		if test -n "$POWERLINE_SUITE_FINAL" ; then
			fail __suite__/enter/final E "Final suites do not allow nesting"
		fi
		export POWERLINE_SUITE_FINAL=1
		# set -x
	fi
}

exit_suite() {
	if test "$POWERLINE_CURRENT_SUITE" = "$POWERLINE_TMP_DIR_SUITE" ; then
		rm_test_root
	fi
	if test $FAILED -ne 0 ; then
		echo "Suite ${POWERLINE_CURRENT_SUITE} failed, summary:"
		echo "${FAIL_SUMMARY}"
	fi
	set +x
	travis_fold end "$POWERLINE_CURRENT_SUITE"
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE%/*}"
	if test "$1" != "--continue" ; then
		exit $FAILED
	else
		unset POWERLINE_SUITE_FINAL
	fi
}

_fail() {
	local allow_failure=
	if test "$1" = "--allow-failure" ; then
		shift
		allow_failure=A
	fi
	local test_name="$1" ; shift
	local fail_char="$allow_failure$1" ; shift
	local message="$1" ; shift
	local verb="$1" ; shift
	local full_msg="$fail_char $POWERLINE_CURRENT_SUITE|$test_name :: $message"
	FAIL_SUMMARY="${FAIL_SUMMARY}${NL}${full_msg}"
	echo "$verb: $full_msg"
	echo "$full_msg" >> "$FAILURES_FILE"
	if test -z "$allow_failure" ; then
		FAILED=1
	fi
}

fail() {
	_fail "$@" "Failed"
}

skip() {
	local test_name="$1" ; shift
	local message="$1" ; shift
	_fail --allow-failure "$test_name" S "$message" "Skipped"
}

make_test_root() {
	local suffix="${POWERLINE_CURRENT_SUITE##*/}"

	local tmpdir="$TMP_ROOT/$suffix/"
	export POWERLINE_TMP_DIR_SUITE="$POWERLINE_CURRENT_SUITE"

	if test -d "$tmpdir" ; then
		rm -r "$tmpdir"
	fi

	mkdir -p "$tmpdir"

	export TEST_ROOT="$tmpdir"
}

rm_test_root() {
	if test -e "$FAILURES_FILE" ; then
		return 0
	fi
	local suffix="${POWERLINE_CURRENT_SUITE##*/}"
	if test -d "$TMP_ROOT/$suffix" ; then
		rm -r "$TMP_ROOT/$suffix"
		rmdir "$TMP_ROOT" &>/dev/null || true
	fi
}

if ! which realpath ; then
	realpath() {
		$PYTHON -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
	}
fi
