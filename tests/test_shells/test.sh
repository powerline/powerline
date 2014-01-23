#!/bin/sh
FAILED=0
ONLY_SHELL="$1"

check_screen_log() {
	if test -e tests/test_shells/${1}.ok ; then
		diff -u tests/test_shells/${1}.ok tests/shell/screen.log
		return $?
	else
		cat tests/shell/screen.log
		return 1
	fi
}

run_test() {
	SH="$1"
	SESNAME="powerline-shell-test-${SH}-$$"

	test "x$ONLY_SHELL" = "x" || test "x$ONLY_SHELL" = "x$SH" || return 0

	screen -L -c tests/test_shells/screenrc -d -m -S "$SESNAME" \
		env LANG=en_US.UTF-8 BINDFILE="$BINDFILE" "$@"
	screen -S "$SESNAME" -X readreg a tests/test_shells/input.$SH
	# Wait for screen to initialize
	sleep 1s
	screen -S "$SESNAME" -p 0 -X width 300 1
	screen -S "$SESNAME" -p 0 -X logfile tests/shell/screen.log
	screen -S "$SESNAME" -p 0 -X paste a
	# Wait for screen to exit (sending command to non-existing screen session 
	# fails; when launched instance exits corresponding session is deleted)
	while screen -S "$SESNAME" -X blankerprg "" > /dev/null ; do
		sleep 0.1s
	done
	cp tests/shell/screen.log tests/shell/${SH}.full.log
	./tests/test_shells/postproc.py tests/shell/screen.log ${SH}
	cp tests/shell/screen.log tests/shell/${SH}.log
	if ! check_screen_log ${SH} ; then
		# Repeat the diff to make it better viewable in travis output
		check_screen_log ${SH} | cat -v
		echo "Failed ${SH}"
		rm tests/shell/screen.log
		return 1
	fi
	rm tests/shell/screen.log
	return 0
}

test -d tests/shell && rm -r tests/shell
mkdir tests/shell
git init tests/shell/3rd
git --git-dir=tests/shell/3rd/.git checkout -b BRANCH

if ! run_test bash --norc --noprofile -i ; then
	FAILED=1
fi

if ! run_test zsh -f -i ; then
	FAILED=1
fi

export XDG_CONFIG_HOME=/dev/null
if ! run_test fish -i ; then
	FAILED=1
fi

test "x$ONLY_SHELL" = "x" && rm -r tests/shell
exit $FAILED
