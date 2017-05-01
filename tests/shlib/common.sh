. tests/bot-ci/scripts/common/main.sh
set +x

: ${PYTHON:=python}
: ${USER:=`id -un`}
: ${HOME:=`getent passwd $USER | cut -d: -f6`}

export USER HOME

if test -z "$FAILED" ; then
	FAILED=0

	FAIL_SUMMARY=""

	TMP_ROOT="$ROOT/tests/tmp"
	FAILURES_FILE="$ROOT/tests/failures"
fi

enter_suite() {
	local suite_name="$1" ; shift
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE}/$suite_name"
}

exit_suite() {
	if test "$POWERLINE_CURRENT_SUITE" = "$POWERLINE_TMP_DIR_SUITE" ; then
		rm_test_root
	fi
	if test $FAILED -ne 0 ; then
		echo "Suite ${POWERLINE_CURRENT_SUITE} failed, summary:"
		echo "${FAIL_SUMMARY}"
	fi
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE%/*}"
	if test "$1" != "--continue" ; then
		exit $FAILED
	fi
}

fail() {
	local allow_failure=
	if test "$1" = "--allow-failure" ; then
		shift
		allow_failure=A
	fi
	local test_name="$1" ; shift
	local fail_char="$allow_failure$1" ; shift
	local message="$1" ; shift
	local full_msg="$fail_char $POWERLINE_CURRENT_SUITE|$test_name :: $message"
	FAIL_SUMMARY="${FAIL_SUMMARY}${NL}${full_msg}"
	echo "Failed: $full_msg"
	echo "$full_msg" >> "$FAILURES_FILE"
	if test -z "$allow_failure" ; then
		FAILED=1
	fi
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
