# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re
import os
import subprocess

from collections import namedtuple

from powerline.lib.shell import run_cmd


TmuxVersionInfo = namedtuple('TmuxVersionInfo', ('major', 'minor', 'suffix'))


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


def get_tmux_output(pl, *args):
	'''Run tmux command and return its output'''
	return _run_tmux(lambda cmd: run_cmd(pl, cmd), args)


def set_tmux_environment(varname, value, remove=True):
	'''Set tmux global environment variable

	:param str varname:
		Name of the variable to set.
	:param str value:
		Variable value.
	:param bool remove:
		True if variable should be removed from the environment prior to 
		attaching any client (runs ``tmux set-environment -r {varname}``).
	'''
	run_tmux_command('set-environment', '-g', varname, value)
	if remove:
		run_tmux_command('set-environment', '-r', varname)


NON_DIGITS = re.compile('[^0-9]+')
DIGITS = re.compile('[0-9]+')
NON_LETTERS = re.compile('[^a-z]+')


def get_tmux_version(pl):
	version_string = get_tmux_output(pl, '-V')
	_, version_string = version_string.split(' ')
	version_string = version_string.strip()
	major, minor = version_string.split('.')
	suffix = DIGITS.subn('', minor)[0] or None
	minor = NON_DIGITS.subn('', minor)[0]
	return TmuxVersionInfo(int(major), int(minor), suffix)
