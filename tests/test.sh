#!/bin/bash
. tests/shlib/common.sh

enter_suite root

if test "$TRAVIS" = true ; then
	export PATH="$HOME/opt/fish/bin:${PATH}"
	export PATH="$PWD/tests/bot-ci/deps/rc:$PATH"

	if test "$PYTHON_IMPLEMENTATION" = "CPython" ; then
		export PATH="$HOME/opt/zsh-${PYTHON_MM}${USE_UCS2_PYTHON:+-ucs2}/bin:${PATH}"
	fi

	if test -n "$USE_UCS2_PYTHON" ; then
		export LD_LIBRARY_PATH="$HOME/opt/cpython-ucs2-$UCS2_PYTHON_VARIANT/lib${LD_LIBRARY_PATH:+:}$LD_LIBRARY_PATH"
		set +e
		. virtualenvwrapper.sh
		workon cpython-ucs2-$UCS2_PYTHON_VARIANT
		set -e
	else
		LIBRARY_PATH="$(ldd "$(which python)" | grep libpython | sed 's/^.* => //;s/ .*$//')"
		LIBRARY_DIR="$(dirname "${LIBRARY_PATH}")"
		export LD_LIBRARY_PATH="$LIBRARY_DIR${LD_LIBRARY_PATH:+:}$LD_LIBRARY_PATH"
	fi
fi

export PYTHON="${PYTHON:=python}"
export PYTHONPATH="${PYTHONPATH}${PYTHONPATH:+:}`realpath .`"
for script in "$ROOT"/tests/test_*/test.sh ; do
	test_name="${script##*/run_}"
	if ! sh $script ; then
		fail "${test_name%_tests.sh}" F "Failed $script"
	fi
done

if test -e "$FAILURES_FILE" ; then
	echo "Fails and skips summary:"
	cat "$FAILURES_FILE"
	rm "$FAILURES_FILE"
fi

exit_suite
