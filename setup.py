#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import logging
import shlex
import subprocess

from setuptools import setup, find_packages

from powerline.version import get_version

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
try:
	README = open(os.path.join(CURRENT_DIR, 'README.rst'), 'rb').read().decode('utf-8')
except IOError:
	README = ''

OLD_PYTHON = sys.version_info < (2, 7)


def compile_client():
	'''Compile the C powerline-client script.'''

	if hasattr(sys, 'getwindowsversion'):
		raise NotImplementedError()
	else:
		from distutils.ccompiler import new_compiler
		compiler = new_compiler().compiler
		cflags = os.environ.get('CFLAGS', str('-O3'))
		# A normal split would do a split on each space which might be incorrect. The
		# shlex will not split if a space occurs in an arguments value.
		subprocess.check_call(compiler + shlex.split(cflags) + ['client/powerline.c', '-o', 'scripts/powerline'])

try:
	compile_client()
except Exception as e:
	print('Compiling C version of powerline-client failed')
	logging.exception(e)
	# FIXME Catch more specific exceptions
	import shutil
	if hasattr(shutil, 'which'):
		which = shutil.which
	else:
		sys.path.append(CURRENT_DIR)
		from powerline.lib.shell import which
	can_use_scripts = True
	if which('socat') and which('sed') and which('sh'):
		print('Using powerline.sh script instead of C version (requires socat, sed and sh)')
		shutil.copyfile('client/powerline.sh', 'scripts/powerline')
	else:
		print('Using powerline.py script instead of C version')
		shutil.copyfile('client/powerline.py', 'scripts/powerline')
else:
	can_use_scripts = False

setup(
	name='powerline-status',
	version=get_version(),
	description='The ultimate statusline/prompt utility.',
	long_description=README,
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Environment :: Plugins',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: MIT License',
		'Natural Language :: English',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: POSIX',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: Implementation :: CPython',
		'Programming Language :: Python :: Implementation :: PyPy',
	],
	download_url='https://github.com/powerline/powerline/archive/develop.zip',
	author='Kim Silkebaekken',
	author_email='kim.silkebaekken+vim@gmail.com',
	url='https://github.com/powerline/powerline',
	license='MIT',
	# XXX Python 3 doesn’t allow compiled C files to be included in the scripts
	# list below. This is because Python 3 distutils tries to decode the file to
	# ASCII, and fails when powerline-client is a binary.
	#
	# XXX Python 2 fucks up script contents*. Not using it to install scripts
	# any longer.
	# * Consider the following input:
	#     % alias hex1=$'hexdump -e \'"" 1/1 "%02X\n"\''
	#     % diff <(hex1 ./scripts/powerline) <(hex1 ~/.local/bin/powerline)
	#   This will show output like
	#     375c375
	#     < 0D
	#     ---
	#     > 0A
	#   (repeated, with diff segment header numbers growing up).
	#
	# FIXME Current solution does not work with `pip install -e`. Still better
	# then solution that is not working at all.
	scripts=[
		'scripts/powerline-lint',
		'scripts/powerline-daemon',
		'scripts/powerline-render',
		'scripts/powerline-config',
	] + (['scripts/powerline'] if can_use_scripts else []),
	data_files=(None if can_use_scripts else (('bin', ['scripts/powerline']),)),
	keywords='',
	packages=find_packages(exclude=('tests', 'tests.*')),
	include_package_data=True,
	zip_safe=False,
	install_requires=['argparse'] if OLD_PYTHON else [],
	extras_require={
		'docs': [
			'Sphinx',
			'sphinx_rtd_theme',
		],
	},
	test_suite='tests' if not OLD_PYTHON else None,
)
