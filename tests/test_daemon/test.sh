#!/bin/sh
. tests/shlib/common.sh

enter_suite daemon final

export ADDRESS="powerline-ipc-test-$$"
echo "Powerline address: $ADDRESS"
if "$PYTHON" "$ROOT/scripts/powerline-daemon" -s"$ADDRESS" ; then
	sleep 1
	if ! ( \
		"$PYTHON" "$ROOT/client/powerline.py" \
			--socket "$ADDRESS" -p/dev/null shell left \
		| grep "file not found"
	) ; then
		fail "devnull" F "-p/dev/null argument ignored or not treated properly"
	fi
	if ( \
		"$PYTHON" "$ROOT/client/powerline.py" --socket "$ADDRESS" \
			-p"$ROOT/powerline/config_files" shell left \
		| grep "file not found"
	) ; then
		fail "nodevnull" F "-p/dev/null argument remembered while it should not"
	fi
	if ! ( \
		cd "$ROOT/tests/test_daemon" \
		&& "$PYTHON" "$ROOT/client/powerline.py" --socket "$ADDRESS" \
			-p"$ROOT/powerline/config_files" shell left \
		| grep "test_daemon"
	) ; then
		fail "segment" F "Output lacks string “tests”"
	fi
else
	fail "exitcode" E "Daemon exited with status $?"
fi
if "$PYTHON" "$ROOT/scripts/powerline-daemon" -s"$ADDRESS" -k ; then
	:
else
	fail "-k" F "powerline-daemon -k failed with exit code $?"
fi

exit_suite
