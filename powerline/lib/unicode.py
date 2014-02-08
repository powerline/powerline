# vim:fileencoding=utf-8:noet

try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


def u(s):
	if type(s) is unicode:
		return s
	else:
		return unicode(s, 'utf-8')
