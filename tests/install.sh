#!/bin/sh
pip install .
pip install psutil
if python -c 'import sys; sys.exit(1 * (sys.version_info[0] != 2))' ; then
	# Python 2
	pip install mercurial bzr
	if python -c 'import sys; sys.exit(1 * (sys.version_info[1] >= 7))' ; then
		# Python 2.6
		pip install unittest2 argparse
	fi
fi
true
