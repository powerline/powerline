from memoize import memoize  # NOQA
from humanize_bytes import humanize_bytes  # NOQA


def underscore_to_camelcase(string):
	'''Return a underscore_separated_string as CamelCase.'''
	return ''.join(word.capitalize() or '_' for word in string.split('_'))
