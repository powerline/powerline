#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals
import os
import sys
import subprocess
import logging

from setuptools import setup, find_packages

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
		subprocess.check_call(compiler + ['-O3', 'client/powerline.c', '-o', 'scripts/powerline'])

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
		from powerline.lib import which
	if which('socat') and which('sed') and which('sh'):
		print('Using powerline.sh script instead of C version (requires socat, sed and sh)')
		shutil.copyfile('client/powerline.sh', 'scripts/powerline')
		can_use_scripts = True
	else:
		print('Using powerline.py script instead of C version')
		shutil.copyfile('client/powerline.py', 'scripts/powerline')
		can_use_scripts = True
else:
	can_use_scripts = False

setup(
	name='Powerline',
	version='beta',
	description='The ultimate statusline/prompt utility.',
	long_description=README,
	classifiers=[],
	author='Kim Silkebaekken',
	author_email='kim.silkebaekken+vim@gmail.com',
	url='https://github.com/Lokaltog/powerline',
	# XXX Python 3 doesn't allow compiled C files to be included in the scripts 
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
	install_requires=[],
	extras_require={
		'docs': [
			'Sphinx',
			'sphinx_rtd_theme',
		],
	},
	test_suite='tests' if not OLD_PYTHON else None,
)
