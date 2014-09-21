# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import codecs

from powerline.lib.encoding import get_preferred_output_encoding


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str


try:
	from __builtin__ import unichr
except ImportError:
	unichr = chr


def u(s):
	'''Return unicode instance assuming UTF-8 encoded string.
	'''
	if type(s) is unicode:
		return s
	else:
		return unicode(s, 'utf-8')


if sys.version_info < (3,):
	def tointiter(s):
		'''Convert a byte string to the sequence of integers
		'''
		return (ord(c) for c in s)
else:
	def tointiter(s):
		'''Convert a byte string to the sequence of integers
		'''
		return iter(s)


def powerline_decode_error(e):
	if not isinstance(e, UnicodeDecodeError):
		raise NotImplementedError
	return (''.join((
		'<{0:02X}>'.format(c)
		for c in tointiter(e.object[e.start:e.end])
	)), e.end)


codecs.register_error('powerline_decode_error', powerline_decode_error)


last_swe_idx = 0


def register_strwidth_error(strwidth):
	global last_swe_idx
	last_swe_idx += 1

	def powerline_encode_strwidth_error(e):
		if not isinstance(e, UnicodeEncodeError):
			raise NotImplementedError
		return ('?' * strwidth(e.object[e.start:e.end]), e.end)

	ename = 'powerline_encode_strwidth_error_{0}'.format(last_swe_idx)
	codecs.register_error(ename, powerline_encode_strwidth_error)
	return ename


def out_u(s):
	'''Return unicode string suitable for displaying

	Unlike other functions assumes get_preferred_output_encoding() first. Unlike 
	u() does not throw exceptions for invalid unicode strings. Unlike 
	safe_unicode() does throw an exception if object is not a string.
	'''
	if isinstance(s, unicode):
		return s
	elif isinstance(s, bytes):
		return unicode(s, get_preferred_output_encoding(), 'powerline_decode_error')
	else:
		raise TypeError('Expected unicode or bytes instance, got {0}'.format(repr(type(s))))


def safe_unicode(s):
	'''Return unicode instance without raising an exception.

	Order of assumptions:
	* ASCII string or unicode object
	* UTF-8 string
	* Object with __str__() or __repr__() method that returns UTF-8 string or 
	  unicode object (depending on python version)
	* String in powerline.lib.encoding.get_preferred_output_encoding() encoding
	* If everything failed use safe_unicode on last exception with which 
	  everything failed
	'''
	try:
		try:
			return unicode(s)
		except UnicodeDecodeError:
			try:
				return unicode(s, 'utf-8')
			except TypeError:
				return unicode(str(s), 'utf-8')
			except UnicodeDecodeError:
				return unicode(s, get_preferred_output_encoding())
	except Exception as e:
		return safe_unicode(e)


class FailedUnicode(unicode):
	'''Builtin ``unicode`` (``str`` in python 3) subclass indicating fatal 
	error.

	If your code for some reason wants to determine whether `.render()` method 
	failed it should check returned string for being a FailedUnicode instance. 
	Alternatively you could subclass Powerline and override `.render()` method 
	to do what you like in place of catching the exception and returning 
	FailedUnicode.
	'''
	pass


def string(s):
	if type(s) is not str:
		return s.encode('utf-8')
	else:
		return s
