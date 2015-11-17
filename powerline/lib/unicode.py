# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import codecs

from unicodedata import east_asian_width, combining

from powerline.lib.encoding import get_preferred_output_encoding


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str


try:
	from __builtin__ import unichr
except ImportError:
	unichr = chr


if sys.maxunicode < 0x10FFFF:
	_unichr = unichr

	def unichr(ch):
		if ch <= sys.maxunicode:
			return _unichr(ch)
		else:
			ch -= 0x10000
			return _unichr((ch >> 10) + 0xD800) + _unichr((ch & ((1 << 10) - 1)) + 0xDC00)


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
	'''Create new encode errors handling method similar to ``replace``

	Like ``replace`` this method uses question marks in place of the characters 
	that cannot be represented in the requested encoding. Unlike ``replace`` the 
	amount of question marks is identical to the amount of display cells 
	offending character occupies. Thus encoding ``…`` (U+2026, HORIZONTAL 
	ELLIPSIS) to ``latin1`` will emit one question mark, but encoding ``Ａ`` 
	(U+FF21, FULLWIDTH LATIN CAPITAL LETTER A) will emit two question marks.

	Since width of some characters depends on the terminal settings and 
	powerline knows how to respect them a single error handling method cannot be 
	used. Instead of it the generator function is used which takes ``strwidth`` 
	function (function that knows how to compute string width respecting all 
	needed settings) and emits new error handling method name.

	:param function strwidth:
		Function that computs string width measured in display cells the string 
		occupies when displayed.

	:return: New error handling method name.
	'''
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
			if type(s) is bytes:
				return unicode(s, 'ascii')
			else:
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
	'''Builtin ``unicode`` subclass indicating fatal error

	If your code for some reason wants to determine whether `.render()` method 
	failed it should check returned string for being a FailedUnicode instance. 
	Alternatively you could subclass Powerline and override `.render()` method 
	to do what you like in place of catching the exception and returning 
	FailedUnicode.
	'''
	pass


if sys.version_info < (3,):
	def string(s):
		if type(s) is not str:
			return s.encode('utf-8')
		else:
			return s
else:
	def string(s):
		if type(s) is not str:
			return s.decode('utf-8')
		else:
			return s


string.__doc__ = (
	'''Transform ``unicode`` or ``bytes`` object into ``str`` object

	On Python-2 this encodes ``unicode`` to ``bytes`` (which is ``str``) using 
	UTF-8 encoding; on Python-3 this decodes ``bytes`` to ``unicode`` (which is 
	``str``) using UTF-8 encoding.

	Useful for functions that expect an ``str`` object in both unicode versions, 
	not caring about the semantic differences between them in Python-2 and 
	Python-3.
	'''
)


def surrogate_pair_to_character(high, low):
	'''Transform a pair of surrogate codepoints to one codepoint
	'''
	return 0x10000 + ((high - 0xD800) << 10) + (low - 0xDC00)


_strwidth_documentation = (
	'''Compute string width in display cells

	{0}

	:param dict width_data:
		Dictionary which maps east_asian_width property values to strings 
		lengths. It is expected to contain the following keys and values (from 
		`East Asian Width annex <http://www.unicode.org/reports/tr11/>`_):

		===  ======  ===========================================================
		Key  Value   Description
		===  ======  ===========================================================
		F    2       Fullwidth: all characters that are defined as Fullwidth in 
		             the Unicode Standard [Unicode] by having a compatibility 
		             decomposition of type <wide> to characters elsewhere in the 
		             Unicode Standard that are implicitly narrow but unmarked.
		H    1       Halfwidth: all characters that are explicitly defined as 
		             Halfwidth in the Unicode Standard by having a compatibility 
		             decomposition of type <narrow> to characters elsewhere in 
		             the Unicode Standard that are implicitly wide but unmarked, 
		             plus U+20A9 ₩ WON SIGN.
		W    2       Wide: all other characters that are always wide. These 
		             characters occur only in the context of East Asian 
		             typography where they are wide characters (such as the 
		             Unified Han Ideographs or Squared Katakana Symbols). This 
		             category includes characters that have explicit halfwidth 
		             counterparts.
		Na   1       Narrow: characters that are always narrow and have explicit 
		             fullwidth or wide counterparts. These characters are 
		             implicitly narrow in East Asian typography and legacy 
		             character sets because they have explicit fullwidth or wide 
		             counterparts. All of ASCII is an example of East Asian 
		             Narrow characters.
		A    1 or 2  Ambigious: characters that may sometimes be wide and 
		             sometimes narrow. Ambiguous characters require additional 
		             information not contained in the character code to further 
		             resolve their width. This information is usually defined in 
		             terminal setting that should in turn respect glyphs widths 
		             in used fonts. Also see :ref:`ambiwidth configuration 
		             option <config-common-ambiwidth>`.
		N    1       Neutral characters: character that does not occur in legacy 
		             East Asian character sets.
		===  ======  ===========================================================

	:param unicode string:
		String whose width will be calculated.

	:return: unsigned integer.''')


def strwidth_ucs_4(width_data, string):
	return sum(((
		(
			0
		) if combining(symbol) else (
			width_data[east_asian_width(symbol)]
		)
	) for symbol in string))


strwidth_ucs_4.__doc__ = _strwidth_documentation.format(
	'''This version of function expects that characters above 0xFFFF are 
	represented using one symbol. This is only the case in UCS-4 Python builds.

	.. note:
		Even in UCS-4 Python builds it is possible to represent characters above 
		0xFFFF using surrogate pairs. Characters represented this way are not 
		supported.''')


def strwidth_ucs_2(width_data, string):
	return sum(((
		(
			width_data[east_asian_width(string[i - 1] + symbol)]
		) if 0xDC00 <= ord(symbol) <= 0xDFFF else (
			0
		) if combining(symbol) or 0xD800 <= ord(symbol) <= 0xDBFF else (
			width_data[east_asian_width(symbol)]
		)
	) for i, symbol in enumerate(string)))


strwidth_ucs_2.__doc__ = _strwidth_documentation.format(
	'''This version of function expects that characters above 0xFFFF are 
	represented using two symbols forming a surrogate pair, which is the only 
	option in UCS-2 Python builds. It still works correctly in UCS-4 Python 
	builds, but is slower then its UCS-4 counterpart.''')
