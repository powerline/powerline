# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals, print_function

from collections import namedtuple
import os
import subprocess
import re


TmuxVersionInfo = namedtuple('TmuxVersionInfo', ('major', 'minor', 'suffix'))

TMUX_CONFIG_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmux')


def get_tmux_executable_name():
	'''Returns tmux executable name

	It should be defined in POWERLINE_TMUX_EXE environment variable, otherwise 
	it is simply “tmux”.
	'''

	return os.environ.get('POWERLINE_TMUX_EXE', 'tmux')


def _run_tmux(runner, args):
	return runner([get_tmux_executable_name()] + list(args))


def run_tmux_command(*args):
	'''Run tmux command, ignoring the output'''
	_run_tmux(subprocess.check_call, args)


def get_tmux_output(*args):
	'''Run tmux command and return its output'''
	return _run_tmux(subprocess.check_output, args)


NON_DIGITS = re.compile('[^0-9]+')
DIGITS = re.compile('[0-9]+')
NON_LETTERS = re.compile('[^a-z]+')


def get_tmux_version():
	version_string = get_tmux_output('-V')
	_, version_string = version_string.split(' ')
	version_string = version_string.strip()
	major, minor = version_string.split('.')
	suffix = DIGITS.subn('', minor)[0] or None
	minor = NON_DIGITS.subn('', minor)[0]
	return TmuxVersionInfo(int(major), int(minor), suffix)


CONFIG_FILE_NAME = re.compile(r'powerline_tmux_(?P<major>\d+)\.(?P<minor>\d+)(?P<suffix>[a-z]+)?(?:_(?P<mod>plus|minus))?\.conf')
CONFIG_MATCHERS = {
	None: (lambda a, b: a.major == b.major and a.minor == b.minor),
	'plus': (lambda a, b: a[:2] <= b[:2]),
	'minus': (lambda a, b: a[:2] >= b[:2]),
}
CONFIG_PRIORITY = {
	None: 3,
	'plus': 2,
	'minus': 1,
}


def list_all_tmux_configs():
	'''List all version-specific tmux configuration files'''
	directory = TMUX_CONFIG_DIRECTORY
	for root, dirs, files in os.walk(directory):
		dirs[:] = ()
		for fname in files:
			match = CONFIG_FILE_NAME.match(fname)
			if match:
				assert match.group('suffix') is None
				yield (
					os.path.join(root, fname),
					CONFIG_MATCHERS[match.group('mod')],
					CONFIG_PRIORITY[match.group('mod')],
					TmuxVersionInfo(
						int(match.group('major')),
						int(match.group('minor')),
						match.group('suffix'),
					),
				)


def get_tmux_configs(version):
	'''Get tmux configuration suffix given parsed tmux version

	:param TmuxVersionInfo version: Parsed tmux version.
	'''
	for fname, matcher, priority, file_version in list_all_tmux_configs():
		if matcher(file_version, version):
			yield (fname, priority + file_version.minor * 10 + file_version.major * 10000)


def source_tmux_files():
	'''Source relevant version-specific tmux configuration files

	Files are sourced in the following order:
	* First relevant files with older versions are sourced.
	* If files for same versions are to be sourced then first _minus files are 
	  sourced, then _plus files and then files without _minus or _plus suffixes.
	'''
	version = get_tmux_version()
	for fname, priority in sorted(get_tmux_configs(version), key=(lambda v: v[1])):
		run_tmux_command('source', fname)
