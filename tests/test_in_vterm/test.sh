#!/bin/sh
. tests/bot-ci/scripts/common/main.sh
set +x

FAILED=0

rm -rf tests/vterm
mkdir tests/vterm
mkdir tests/vterm/path

ln -s "$(which "${PYTHON}")" tests/vterm/path/python
ln -s "$(which bash)" tests/vterm/path
ln -s "$(which env)" tests/vterm/path
ln -s "$PWD/scripts/powerline-render" tests/vterm/path
ln -s "$PWD/scripts/powerline-config" tests/vterm/path

cp -r tests/terminfo tests/vterm

FAIL_SUMMARY=""

test_tmux() {
	if test "$PYTHON_IMPLEMENTATION" = PyPy && test "$PYTHON_VERSION_MAJOR" -eq 3 ; then
		# FIXME PyPy3 segfaults for some reason
		return 0
	fi
	if ! which "${POWERLINE_TMUX_EXE}" ; then
		return 0
	fi
	ln -sf "$(which "${POWERLINE_TMUX_EXE}")" tests/vterm/path
	f=tests/test_in_vterm/test_tmux.py
	if ! "${PYTHON}" $f ; then
		echo "Failed vterm test $f"
		FAILED=1
		FAIL_SUMMARY="$FAIL_SUMMARY${NL}F $POWERLINE_TMUX_EXE $f"
		for file in tests/vterm/*.log ; do
			if ! test -e "$file" ; then
				break
			fi
			echo '____________________________________________________________'
			echo "$file:"
			echo '============================================================'
			cat -v $file
		done
	fi
}

if test -z "$POWERLINE_TMUX_EXE" && test -d tests/bot-ci/deps/tmux ; then
	for tmux in tests/bot-ci/deps/tmux/tmux-*/tmux ; do
		export POWERLINE_TMUX_EXE="$PWD/$tmux"
		if test_tmux ; then
			rm -f tests/vterm/*.log
		fi
	done
else
	test_tmux || true
fi

if test $FAILED -eq 0 ; then
	echo "$FAIL_SUMMARY"
	rm -rf tests/vterm
fi

exit $FAILED
