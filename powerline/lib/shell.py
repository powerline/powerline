# vim:fileencoding=utf-8:noet

from __future__ import absolute_import, unicode_literals, division, print_function

from subprocess import Popen, PIPE
from locale import getlocale, getdefaultlocale, LC_MESSAGES
from functools import partial
import sys


if sys.platform.startswith('win32'):
	# Prevent windows from launching consoles when calling commands
	# http://msdn.microsoft.com/en-us/library/windows/desktop/ms684863(v=vs.85).aspx
	Popen = partial(Popen, creationflags=0x08000000)


def _get_shell_encoding():
	return getlocale(LC_MESSAGES)[1] or getdefaultlocale()[1] or 'utf-8'


def run_cmd(pl, cmd, stdin=None):
	'''Run command and return its stdout, stripped

	If running command fails returns None and logs failure to ``pl`` argument.

	:param PowerlineLogger pl:
		Logger used to log failures.
	:param list cmd:
		Command which will be run.
	:param str stdin:
		String passed to command. May be None.
	'''
	try:
		p = Popen(cmd, shell=False, stdout=PIPE, stdin=PIPE)
	except OSError as e:
		pl.exception('Could not execute command ({0}): {1}', e, cmd)
		return None
	else:
		stdout, err = p.communicate(stdin)
		stdout = stdout.decode(_get_shell_encoding())
	return stdout.strip()


def asrun(pl, ascript):
	'''Run the given AppleScript and return the standard output and error.'''
	return run_cmd(pl, ['osascript', '-'], ascript)


def readlines(cmd, cwd):
	'''Run command and read its output, line by line

	:param list cmd:
		Command which will be run.
	:param str cwd:
		Working directory of the command which will be run.
	'''
	p = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE, cwd=cwd)
	encoding = _get_shell_encoding()
	p.stderr.close()
	with p.stdout:
		for line in p.stdout:
			yield line[:-1].decode(encoding)
