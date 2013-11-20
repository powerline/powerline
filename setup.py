#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals
import os
import sys
import subprocess

from setuptools import setup, find_packages

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
try:
	README = open(os.path.join(CURRENT_DIR, 'README.rst'), 'rb').read().decode('utf-8')
except IOError:
	README = ''

OLD_PYTHON = sys.version_info < (2, 7)
PYTHON_3 = sys.version_info > (2,)


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
except Exception:
	# FIXME Catch more specific exceptions
	import shutil
	print('Compiling C version of powerline-client failed, using Python version instead')
	shutil.copyfile('client/powerline.py', 'scripts/powerline')

setup(
	name='Powerline',
	version='beta',
	description='The ultimate statusline/prompt utility.',
	long_description=README,
	classifiers=[],
	author='Kim Silkebaekken',
	author_email='kim.silkebaekken+vim@gmail.com',
	url='https://github.com/Lokaltog/powerline',
	# FIXME Python 3 doesn't allow compiled C files to be included in the 
	# scripts list below. This is because Python 3 distutils tries to decode the 
	# file to ASCII, and fails when powerline-client is a binary.
	scripts=[
		'scripts/powerline-lint',
		'scripts/powerline-daemon',
		'scripts/powerline-render',
		'scripts/powerline-config',
	] + ([] if PYTHON_3 else ['scripts/powerline']),
	data_files=([('bin', ['scripts/powerline'])] if PYTHON_3 else None),
	keywords='',
	packages=find_packages(exclude=('tests', 'tests.*')),
	include_package_data=True,
	zip_safe=False,
	install_requires=[],
	extras_require={
		'docs': [
			'Sphinx',
		],
	},
	test_suite='tests' if not OLD_PYTHON else None,
)
