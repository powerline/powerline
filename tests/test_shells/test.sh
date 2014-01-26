#!/bin/sh
FAILED=0
ONLY_SHELL="$1"

check_screen_log() {
	SH="$1"
	if test -e tests/test_shells/${SH}.ok ; then
		diff -u tests/test_shells/${SH}.ok tests/shell/${SH}.log
		return $?
	else
		cat tests/shell/${SH}.log
		return 1
	fi
}

run_test() {
	SH="$1"
	SESNAME="powerline-shell-test-${SH}-$$"

	test "x$ONLY_SHELL" = "x" || test "x$ONLY_SHELL" = "x$SH" || return 0

	which "${SH}" || return 0

	export SH

	screen -L -c tests/test_shells/screenrc -d -m -S "$SESNAME" \
		env LANG=en_US.UTF-8 BINDFILE="$BINDFILE" "$@"
	screen -S "$SESNAME" -X readreg a tests/test_shells/input.$SH
	# Wait for screen to initialize
	sleep 1s
	screen -S "$SESNAME" -p 0 -X width 300 1
	screen -S "$SESNAME" -p 0 -X paste a
	# Wait for screen to exit (sending command to non-existing screen session 
	# fails; when launched instance exits corresponding session is deleted)
	while screen -S "$SESNAME" -X blankerprg "" > /dev/null ; do
		sleep 0.1s
	done
	./tests/test_shells/postproc.py ${SH}
	if ! check_screen_log ${SH} ; then
		echo '____________________________________________________________'
		# Repeat the diff to make it better viewable in travis output
		echo "Diff (cat -v):"
		echo '============================================================'
		check_screen_log ${SH} | cat -v
		echo '____________________________________________________________'
		echo "Failed ${SH}. Full output:"
		echo '============================================================'
		cat tests/shell/${SH}.full.log
		echo '____________________________________________________________'
		echo "Full output (cat -v):"
		echo '============================================================'
		cat -v tests/shell/${SH}.full.log
		echo '____________________________________________________________'
		${SH} --version
		return 1
	fi
	return 0
}

test -d tests/shell && rm -r tests/shell
mkdir tests/shell
git init tests/shell/3rd
git --git-dir=tests/shell/3rd/.git checkout -b BRANCH
export DIR1="[32m"
export DIR2=""
mkdir tests/shell/3rd/"$DIR1"
mkdir tests/shell/3rd/"$DIR2"
mkdir tests/shell/3rd/'\[\]'
mkdir tests/shell/3rd/'%%'
mkdir tests/shell/3rd/'#[bold]'
mkdir tests/shell/3rd/'(echo)'
mkdir tests/shell/3rd/'$(echo)'
mkdir tests/shell/3rd/'`echo`'

if ! run_test bash --norc --noprofile -i ; then
	FAILED=1
fi

if ! run_test zsh -f -i ; then
	FAILED=1
fi

mkdir tests/shell/fish_home
export XDG_CONFIG_HOME="$PWD/tests/shell/fish_home"
if ! run_test fish -i ; then
	FAILED=1
fi

if ! run_test tcsh -f -i ; then
	FAILED=1
fi

test "x$ONLY_SHELL" = "x" && rm -r tests/shell
exit $FAILED
