#!/bin/sh
. tests/common.sh

enter_suite daemon

export ADDRESS="powerline-ipc-test-$$"
echo "Powerline address: $ADDRESS"
if $PYTHON scripts/powerline-daemon -s$ADDRESS ; then
	sleep 1
	if ! ( \
		$PYTHON client/powerline.py --socket $ADDRESS -p/dev/null shell left | \
		grep 'file not found'
	) ; then
		fail "devnull" F "-p/dev/null argument ignored or not treated properly"
	fi
	if ( \
		$PYTHON client/powerline.py --socket $ADDRESS \
			-p$PWD/powerline/config_files shell left | \
		grep 'file not found'
	) ; then
		fail "nodevnull" F "-p/dev/null argument remembered while it should not"
	fi
	if ! ( \
		cd tests && \
		$PYTHON ../client/powerline.py --socket $ADDRESS \
			-p$PWD/../powerline/config_files shell left | \
		grep 'tests'
	) ; then
		fail "segment" F "Output lacks string “tests”"
	fi
else
	fail "exitcode" E "Daemon exited with status $?"
fi
if $PYTHON scripts/powerline-daemon -s$ADDRESS -k ; then
	:
else
	fail "-k" F "powerline-daemon -k failed with exit code $?"
fi

exit_suite
