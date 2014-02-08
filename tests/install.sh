#!/bin/sh
pip install .
pip install psutil
if python -c 'import sys; sys.exit(1 * (sys.version_info[0] != 2))' ; then
	# Python 2
	pip install mercurial
	pip install --allow-external bzr --allow-unverified bzr bzr
	if python -c 'import sys; sys.exit(1 * (sys.version_info[1] >= 7))' ; then
		# Python 2.6
		pip install unittest2 argparse
	fi
fi
sudo apt-get install -qq screen zsh tcsh
# Travis has too outdated fish. It cannot be used for tests.
# sudo apt-get install fish
true
