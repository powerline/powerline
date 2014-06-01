# vim:fileencoding=utf-8:noet

from subprocess import Popen, PIPE
from locale import getlocale, getdefaultlocale, LC_MESSAGES


def run_cmd(pl, cmd, stdin=None):
	try:
		p = Popen(cmd, stdout=PIPE, stdin=PIPE)
	except OSError as e:
		pl.exception('Could not execute command ({0}): {1}', e, cmd)
		return None
	else:
		stdout, err = p.communicate(stdin)
		encoding = getlocale(LC_MESSAGES)[1] or getdefaultlocale()[1] or 'utf-8'
		stdout = stdout.decode(encoding)
	return stdout.strip()


def asrun(pl, ascript):
	'''Run the given AppleScript and return the standard output and error.'''
	return run_cmd(pl, ['osascript', '-'], ascript)
