. tests/shlib/common.sh
set +x

vterm_setup() {
	make_test_root

	mkdir "$TEST_ROOT/path"

	ln -s "$(which "${PYTHON}")" "$TEST_ROOT/path/python"
	ln -s "$(which bash)" "$TEST_ROOT/path"

	cp -r "$ROOT/tests/terminfo" "$TEST_ROOT"
}

vterm_shutdown() {
	rm_test_root
}
