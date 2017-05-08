. tests/shlib/common.sh
. tests/bot-ci/scripts/common/main.sh
set +x

vterm_setup() {
	local test_dir="$1" ; shift

	rm -rf "$test_dir"
	mkdir "$test_dir"
	mkdir "$test_dir/path"

	ln -s "$(which "${PYTHON}")" "$test_dir/path/python"
	ln -s "$(which bash)" "$test_dir/path"

	cp -r "$ROOT/tests/terminfo" "$test_dir"
}

vterm_shutdown() {
	local test_dir="$1" ; shift

	if test $FAILED -eq 0 ; then
		rm -rf "$test_dir"
	else
		echo "$FAIL_SUMMARY"
	fi
}
