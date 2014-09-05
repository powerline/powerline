#!/usr/bin/env python
# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import argparse
import codecs
import os

from subprocess import check_output, check_call


def parse_version(s):
	if s == ('+' * len(s)):
		try:
			last_version = next(iter(sorted([
				tuple(map(int, tag.split('.')))
				for tag in check_output(['git', 'tag', '-l', '[0-9]*.*']).split('\n')[:-1]
			], reverse=True)))
		except StopIteration:
			raise ValueError('No existing versions found')

		version = []
		for i in range(len(s) - 1):
			try:
				version.append(last_version[i])
			except IndexError:
				version.append(0)

		try:
			version.append(last_version[len(s) - 1] + 1)
		except IndexError:
			version.append(1)

		if len(version) == 1:
			version.append(0)

		return tuple(version)
	else:
		return tuple(map(int, s.split('.')))


p = argparse.ArgumentParser(description='Powerline release script')
p.add_argument('-v', '--version', type=parse_version, metavar='VERSION', help='Use given version for the release. If version contains only `+\' signs then it will increase latest version number: one `+\' increases major version number (e.g. 1.2.3 -> 2.0), `++\' increases minor version number (e.g. 1.2.3 -> 1.3), `+++\' increases patch level (e.g. 1.2.3 -> 1.2.4). Defaults to `+++\'', default='+++')
p.add_argument('-r', '--rev', metavar='COMMIT', help='Use given revision for the release. Defaults to `develop\'.', default='develop')


def create_release(version, rev):
	version_string = '.'.join((str(v) for v in version))
	check_call(['git', 'checkout', 'master'])
	check_call(['git', 'merge', '--no-ff', '--no-commit', '--log', rev])

	with codecs.open('.setup.py.new', 'w', encoding='utf-8') as NS:
		with codecs.open('setup.py', 'r', encoding='utf-8') as OS:
			for line in OS:
				if line.startswith('\tversion='):
					line = '\tversion=\'' + version_string + '\',\n'
				elif 'Development Status' in line:
					line = '\t\t\'Development Status :: 5 - Production/Stable\',\n'
				NS.write(line)

	os.unlink('setup.py')
	os.rename('.setup.py.new', 'setup.py')
	check_call(['git', 'add', 'setup.py'])

	check_call(['git', 'commit'])
	check_call(['git', 'tag', '-m', 'Release ' + version_string, '-a', version_string])
	check_call(['git', 'push', 'upstream', 'master'])
	check_call(['git', 'push', 'upstream', version_string])
	check_call(['python', 'setup.py', 'sdist', 'upload'])
	check_call(['python', 'setup.py', 'upload_docs'])


if __name__ == '__main__':
	args = p.parse_args()
	create_release(args.version, args.rev)
