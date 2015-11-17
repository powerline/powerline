# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import os

from subprocess import Popen, PIPE
from functools import partial

from powerline.lib.encoding import get_preferred_input_encoding


if sys.platform.startswith('win32'):
	# Prevent windows from launching consoles when calling commands
	# http://msdn.microsoft.com/en-us/library/windows/desktop/ms684863(v=vs.85).aspx
	Popen = partial(Popen, creationflags=0x08000000)


def run_cmd(pl, cmd, stdin=None, strip=True):
	'''Run command and return its stdout, stripped

	If running command fails returns None and logs failure to ``pl`` argument.

	:param PowerlineLogger pl:
		Logger used to log failures.
	:param list cmd:
		Command which will be run.
	:param str stdin:
		String passed to command. May be None.
	:param bool strip:
		True if the result should be stripped.
	'''
	try:
		p = Popen(cmd, shell=False, stdout=PIPE, stdin=PIPE)
	except OSError as e:
		pl.exception('Could not execute command ({0}): {1}', e, cmd)
		return None
	else:
		stdout, err = p.communicate(stdin)
		stdout = stdout.decode(get_preferred_input_encoding())
	return stdout.strip() if strip else stdout


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
	encoding = get_preferred_input_encoding()
	p.stderr.close()
	with p.stdout:
		for line in p.stdout:
			yield line[:-1].decode(encoding)


try:
	from shutil import which
except ImportError:
	# shutil.which was added in python-3.3. Here is what was added:
	# Lib/shutil.py, commit 5abe28a9c8fe701ba19b1db5190863384e96c798
	def which(cmd, mode=os.F_OK | os.X_OK, path=None):
		'''Given a command, mode, and a PATH string, return the path which 
		conforms to the given mode on the PATH, or None if there is no such 
		file.

		``mode`` defaults to os.F_OK | os.X_OK. ``path`` defaults to the result 
		of ``os.environ.get('PATH')``, or can be overridden with a custom search 
		path.
		'''
		# Check that a given file can be accessed with the correct mode.
		# Additionally check that `file` is not a directory, as on Windows
		# directories pass the os.access check.
		def _access_check(fn, mode):
			return (
				os.path.exists(fn)
				and os.access(fn, mode)
				and not os.path.isdir(fn)
			)

		# If we’re given a path with a directory part, look it up directly rather
		# than referring to PATH directories. This includes checking relative to the
		# current directory, e.g. ./script
		if os.path.dirname(cmd):
			if _access_check(cmd, mode):
				return cmd
			return None

		if path is None:
			path = os.environ.get('PATH', os.defpath)
		if not path:
			return None
		path = path.split(os.pathsep)

		if sys.platform == 'win32':
			# The current directory takes precedence on Windows.
			if os.curdir not in path:
				path.insert(0, os.curdir)

			# PATHEXT is necessary to check on Windows.
			pathext = os.environ.get('PATHEXT', '').split(os.pathsep)
			# See if the given file matches any of the expected path extensions.
			# This will allow us to short circuit when given 'python.exe'.
			# If it does match, only test that one, otherwise we have to try
			# others.
			if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
				files = [cmd]
			else:
				files = [cmd + ext for ext in pathext]
		else:
			# On other platforms you don’t have things like PATHEXT to tell you
			# what file suffixes are executable, so just pass on cmd as-is.
			files = [cmd]

		seen = set()
		for dir in path:
			normdir = os.path.normcase(dir)
			if normdir not in seen:
				seen.add(normdir)
				for thefile in files:
					name = os.path.join(dir, thefile)
					if _access_check(name, mode):
						return name
		return None
