#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
	README = open(os.path.join(here, 'README.rst')).read()
except IOError:
	README = ''

old_python = sys.version_info < (2, 7)

setup(
	name='Powerline',
	version='beta',
	description='The ultimate statusline/prompt utility.',
	long_description=README,
	classifiers=[],
	author='Kim Silkebækken',
	author_email='kim.silkebaekken+vim@gmail.com',
	url='https://github.com/Lokaltog/powerline',
	scripts=[
		'scripts/powerline',
		],
	keywords='',
	packages=find_packages(exclude=('tests',)),
	include_package_data=True,
	zip_safe=False,
	install_requires=[],
	extras_require={
		'docs': [
			'Sphinx',
			],
		},
	test_suite='tests' if not old_python else None,
	)
