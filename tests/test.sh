#!/bin/bash
. tests/bot-ci/scripts/common/main.sh

: ${USER:=`id -un`}
: ${HOME:=`getent passwd $USER | cut -d: -f6`}

export USER HOME

FAILED=0

if test "$TRAVIS" = true ; then
	export PATH="$HOME/opt/fish/bin:${PATH}"
	export PATH="$PWD/tests/bot-ci/deps/rc:$PATH"
	export PATH="$PWD/tests/bot-ci/deps/mksh:$PATH"
	export PATH="$PWD/tests/bot-ci/deps/busybox:$PATH"
	export PATH="$PWD/tests/bot-ci/deps/tcsh:$PATH"
	export PATH="$PWD/tests/bot-ci/deps/socat:$PATH"

	if test "$PYTHON_IMPLEMENTATION" = "CPython" ; then
		export PATH="$HOME/opt/zsh-${PYTHON_MM}${USE_UCS2_PYTHON:+-ucs2}/bin:${PATH}"
	fi

	if test -n "$USE_UCS2_PYTHON" ; then
		export LD_LIBRARY_PATH="$HOME/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib${LD_LIBRARY_PATH:+:}$LD_LIBRARY_PATH"
		set +e
		. virtualenvwrapper.sh
		workon cpython-ucs2-$UCS2_PYTHON_VARIANT
		set -e
	fi
fi

if ! which realpath ; then
	realpath() {
		$PYTHON -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
	}
fi

export PYTHON="${PYTHON:=python}"
export PYTHONPATH="${PYTHONPATH}${PYTHONPATH:+:}`realpath .`"
for script in tests/run_*_tests.sh ; do
	if ! sh $script ; then
		echo "Failed $script"
		FAILED=1
	fi
done
exit $FAILED
