from powerline.lib.memoize import memoize  # NOQA
from powerline.lib.humanize_bytes import humanize_bytes  # NOQA
from powerline.lib.url import urllib_read, urllib_urlencode  # NOQA


def underscore_to_camelcase(string):
	'''Return a underscore_separated_string as CamelCase.'''
	return ''.join(word.capitalize() or '_' for word in string.split('_'))


def mergedicts(d1, d2):
	'''Recursively merge two dictionaries. First dictionary is modified in-place.
	'''
	for k in d2:
		if k in d1 and type(d1[k]) is dict and type(d2[k]) is dict:
			mergedicts(d1[k], d2[k])
		else:
			d1[k] = d2[k]
