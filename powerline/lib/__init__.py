from powerline.lib.memoize import memoize  # NOQA
from powerline.lib.humanize_bytes import humanize_bytes  # NOQA
from powerline.lib.url import urllib_read, urllib_urlencode  # NOQA


def underscore_to_camelcase(string):
	'''Return a underscore_separated_string as CamelCase.'''
	return ''.join(word.capitalize() or '_' for word in string.split('_'))
