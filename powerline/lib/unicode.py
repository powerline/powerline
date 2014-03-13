# vim:fileencoding=utf-8:noet


from locale import getpreferredencoding


try:
	from __builtin__ import unicode
except ImportError:
	unicode = str  # NOQA


def u(s):
	'''Return unicode instance assuming UTF-8 encoded string.
	'''
	if type(s) is unicode:
		return s
	else:
		return unicode(s, 'utf-8')


def safe_unicode(s):
	'''Return unicode instance without raising an exception.

	Order of assumptions:
	* ASCII string or unicode object
	* UTF-8 string
	* Object with __str__() or __repr__() method that returns UTF-8 string or 
	  unicode object (depending on python version)
	* String in locale.getpreferredencoding() encoding
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
				return unicode(s, getpreferredencoding())
	except Exception as e:
		return safe_unicode(e)
