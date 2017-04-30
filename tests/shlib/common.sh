. tests/bot-ci/scripts/common/main.sh
set +x

: ${PYTHON:=python}

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
	rm_tmp_dir
	if test $FAILED -ne 0 ; then
		echo "Suite ${POWERLINE_CURRENT_SUITE} failed, summary:"
		echo "${FAIL_SUMMARY}"
	fi
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE%/*}"
	if test "x$1" != "x--continue" ; then
		exit $FAILED
	fi
}

fail() {
	local allow_failure=
	if test "x$1" = "x--allow-failure" ; then
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
	if test "x$allow_failure" = "x" ; then
		FAILED=1
	fi
}

make_tmp_dir() {
	local suffix="$1" ; shift

	local tmpdir="$TMP_ROOT/$suffix/"

	if test -d "$tmpdir" ; then
		rm -r "$tmpdir"
	fi

	mkdir -p "$tmpdir"

	printf '%s' "$tmpdir"
}

rm_tmp_dir() {
	if test -e "$FAILURES_FILE" ; then
		return 0
	fi
	if test -d "$TMP_ROOT" ; then
		rm -r "$TMP_ROOT"
	fi
}
