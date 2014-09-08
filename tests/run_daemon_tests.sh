#!/bin/sh
FAILED=0
export ADDRESS="powerline-ipc-test-$$"
echo "Powerline address: $ADDRESS"
if $PYTHON scripts/powerline-daemon -s$ADDRESS ; then
	sleep 1
	if ! ( \
		$PYTHON client/powerline.py --socket $ADDRESS -p/dev/null shell left | \
		grep 'file not found'
	) ; then
		echo "-p/dev/null argument ignored or not treated properly"
		FAILED=1
	fi
	if ( \
		$PYTHON client/powerline.py --socket $ADDRESS \
			-p$PWD/powerline/config_files shell left | \
		grep 'file not found'
	) ; then
		echo "-p/dev/null argument remembered while it should not"
		FAILED=1
	fi
	if ! ( \
		cd tests && \
		$PYTHON ../client/powerline.py --socket $ADDRESS \
			-p$PWD/../powerline/config_files shell left | \
		grep 'tests'
	) ; then
		echo "Output lacks string “tests”"
		FAILED=1
	fi
else
	echo "Daemon exited with status $?"
	FAILED=1
fi
if $PYTHON scripts/powerline-daemon -s$ADDRESS -k ; then
	:
else
	echo "powerline-daemon -k failed with exit code $?"
	FAILED=1
fi
exit $FAILED
