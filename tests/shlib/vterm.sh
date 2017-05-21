. tests/shlib/common.sh
set +x

vterm_setup() {
	local vterm_suf="$1" ; shift

	make_test_root "vterm_$vterm_suf"

	mkdir "$TEST_ROOT/path"

	ln -s "$(which "${PYTHON}")" "$TEST_ROOT/path/python"
	ln -s "$(which bash)" "$TEST_ROOT/path"

	cp -r "$ROOT/tests/terminfo" "$TEST_ROOT"
}

vterm_shutdown() {
	rm_test_root
}
