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
	return (
		locale.getlocale(locale.LC_MESSAGES)[1]
		or locale.getdefaultlocale()[1]
		or 'ascii'
	)


def get_preferred_input_encoding():
	'''Get encoding that should be used for reading shell command output

	.. warning::
		Falls back to latin1 so that function is less likely to throw as decoded 
		output is primary searched for ASCII values.
	'''
	return (
		locale.getlocale(locale.LC_MESSAGES)[1]
		or locale.getdefaultlocale()[1]
		or 'latin1'
	)


def get_preferred_environment_encoding():
	'''Get encoding that should be used for decoding environment variables
	'''
	return (
		locale.getpreferredencoding()
		or 'utf-8'
	)
