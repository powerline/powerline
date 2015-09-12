. tests/bot-ci/scripts/common/main.sh
set +x

: ${PYTHON:=python}

FAILED=0

FAIL_SUMMARY=""

enter_suite() {
	local suite_name="$1"
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE}/$suite_name"
}

exit_suite() {
	if test $FAILED -ne 0 ; then
		echo "Suite ${POWERLINE_CURRENT_SUITE} failed, summary:"
		echo "${FAIL_SUMMARY}"
	fi
	export POWERLINE_CURRENT_SUITE="${POWERLINE_CURRENT_SUITE%/*}"
	exit $FAILED
}

fail() {
	local test_name="$1"
	local fail_char="$2"
	local message="$3"
	local full_msg="$fail_char $POWERLINE_CURRENT_SUITE|$test_name :: $message"
	FAIL_SUMMARY="${FAIL_SUMMARY}${NL}${full_msg}"
	echo "Failed: $full_msg"
	echo "$full_msg" >> tests/status
	FAILED=1
}

skip() {
	local test_name="$1"
	local message="$2"
	local full_msg="S $POWERLINE_CURRENT_SUITE|$test_name :: $message"
	echo "Skipped: $full_msg"
	echo "$full_msg" >> tests/status
}
