#!/bin/sh
FAILED=0

if [ "$(echo '\e')" != '\e' ] ; then
	safe_echo() {
		echo -E "$@"
	}
else
	safe_echo() {
		echo "$@"
	}
fi

run_test() {
	SESNAME="powerline-shell-test-$$"
	screen -L -c tests/test_shells/screenrc -d -m -S "$SESNAME" env LANG=C "$@"
	screen -S "$SESNAME" -X readreg a tests/test_shells/input.sh
	sleep 5s
	screen -S "$SESNAME" -p 0 -X width 300 1
	screen -S "$SESNAME" -p 0 -X logfile tests/shell/screen.log
	screen -S "$SESNAME" -p 0 -X paste a
	while screen -S "$SESNAME" -X blankerprg "" > /dev/null ; do
		sleep 1s
	done
	sed -i -e "1,3 d" \
	       -e s/$(cat tests/shell/3rd/pid)/PID/g \
	       -e "s/$(python -c 'import re, socket; print (re.escape(socket.gethostname()))')/HOSTNAME/g" \
	       tests/shell/screen.log
	if ! diff -u tests/test_shells/${1}.ok tests/shell/screen.log ; then
		return 1
	fi
	return 0
}

mkdir tests/shell
git init tests/shell/3rd
git --git-dir=tests/shell/3rd/.git checkout -b BRANCH

if ! run_test bash --norc --noprofile -i ; then
	echo "Failed bash"
	FAILED=1
fi
rm -r tests/shell
exit $FAILED
