#!/bin/sh
: ${PYTHON:=python}
: ${POWERLINE_TMUX_EXE:=tmux}

set -e

# HACK: get newline for use in strings given that "\n" and $'' do not work.
NL="$(printf '\nE')"
NL="${NL%E}"

FAILED=0

rm -rf tests/vterm
mkdir tests/vterm
mkdir tests/vterm/path

ln -s "$(which "${PYTHON}")" tests/vterm/path/python
ln -s "$(which bash)" tests/vterm/path
ln -s "$(which env)" tests/vterm/path
ln -s "$PWD/scripts/powerline-render" tests/vterm/path
ln -s "$PWD/scripts/powerline-config" tests/vterm/path

FAIL_SUMMARY=""

test_tmux() {
	if ! which "${POWERLINE_TMUX_EXE}" ; then
		return 0
	fi
	ln -s "$(which "${POWERLINE_TMUX_EXE}")" tests/vterm/path
	if ! "${PYTHON}" tests/test_in_vterm/test_tmux.py; then
		echo "Failed vterm test $f"
		FAILED=1
		FAIL_SUMMARY="$FAIL_SUMMARY${NL}F $f"
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

test_tmux || true

if test $FAILED -eq 0 ; then
	echo "$FAIL_SUMMARY"
	rm -rf tests/vterm
fi

exit $FAILED
