#!/bin/sh
pip install .
pip install psutil
if python -c 'import sys; sys.exit(1 * (sys.version_info[0] != 2))' ; then
	# Python 2
	if python -c 'import platform, sys; sys.exit(1 - (platform.python_implementation() == "CPython"))' ; then
		pip install mercurial
		pip install --allow-external bzr --allow-unverified bzr bzr
	fi
	if python -c 'import sys; sys.exit(1 * (sys.version_info[1] >= 7))' ; then
		# Python 2.6
		pip install unittest2 argparse
	fi
fi
sudo apt-get install -qq screen zsh tcsh mksh busybox
# Travis has too outdated fish. It cannot be used for tests.
# sudo apt-get install fish
true
