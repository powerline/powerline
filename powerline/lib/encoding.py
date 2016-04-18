# vim:fileencoding=utf-8:noet

'''Encodings support

This is the only module from which functions obtaining encoding should be 
exported. Note: you should always care about errors= argument since it is not 
guaranteed that encoding returned by some function can encode/decode given 
string.

All functions in this module must always return a valid encoding. Most of them 
are not thread-safe.
'''

from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import locale


def get_preferred_file_name_encoding():
	'''Get preferred file name encoding
	'''
	return (
		sys.getfilesystemencoding()
		or locale.getpreferredencoding()
		or 'utf-8'
	)


def get_preferred_file_contents_encoding():
	'''Get encoding preferred for file contents
	'''
	return (
		locale.getpreferredencoding()
		or 'utf-8'
	)


def get_preferred_output_encoding():
	'''Get encoding that should be used for printing strings

	.. warning::
		Falls back to ASCII, so that output is most likely to be displayed 
		correctly.
	'''
	if hasattr(locale, 'LC_MESSAGES'):
		return (
			locale.getlocale(locale.LC_MESSAGES)[1]
			or locale.getdefaultlocale()[1]
			or 'ascii'
		)

	return (
		locale.getdefaultlocale()[1]
		or 'ascii'
	)


def get_preferred_input_encoding():
	'''Get encoding that should be used for reading shell command output

	.. warning::
		Falls back to latin1 so that function is less likely to throw as decoded 
		output is primary searched for ASCII values.
	'''
	if hasattr(locale, 'LC_MESSAGES'):
		return (
			locale.getlocale(locale.LC_MESSAGES)[1]
			or locale.getdefaultlocale()[1]
			or 'latin1'
		)

	return (
		locale.getdefaultlocale()[1]
		or 'latin1'
	)


def get_preferred_arguments_encoding():
	'''Get encoding that should be used for command-line arguments

	.. warning::
		Falls back to latin1 so that function is less likely to throw as 
		non-ASCII command-line arguments most likely contain non-ASCII 
		filenames and screwing them up due to unidentified locale is not much of 
		a problem.
	'''
	return (
		locale.getdefaultlocale()[1]
		or 'latin1'
	)


def get_preferred_environment_encoding():
	'''Get encoding that should be used for decoding environment variables
	'''
	return (
		locale.getpreferredencoding()
		or 'utf-8'
	)


def get_unicode_writer(stream=sys.stdout, encoding=None, errors='replace'):
	'''Get function which will write unicode string to the given stream

	Writing is done using encoding returned by 
	:py:func:`get_preferred_output_encoding`.

	:param file stream:
		Stream to write to. Default value is :py:attr:`sys.stdout`.
	:param str encoding:
		Determines which encoding to use. If this argument is specified then 
		:py:func:`get_preferred_output_encoding` is not used.
	:param str errors:
		Determines what to do with characters which cannot be encoded. See 
		``errors`` argument of :py:func:`codecs.encode`.

	:return: Callable which writes unicode string to the given stream using 
	         the preferred output encoding.
	'''
	encoding = encoding or get_preferred_output_encoding()
	if sys.version_info < (3,) or not hasattr(stream, 'buffer'):
		return lambda s: stream.write(s.encode(encoding, errors))
	else:
		return lambda s: stream.buffer.write(s.encode(encoding, errors))
