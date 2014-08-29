#!/bin/sh
FAILED=0
if ! ${PYTHON} scripts/powerline-lint -p powerline/config_files ; then
	echo "Failed powerline-lint"
	FAILED=1
fi
exit $FAILED
