# vim:fileencoding=utf-8:noet
from functools import wraps
import json

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


def add_divider_highlight_group(highlight_group):
	def dec(func):
		@wraps(func)
		def f(**kwargs):
			r = func(**kwargs)
			if r:
				return [{
					'contents': r,
					'divider_highlight_group': highlight_group,
				}]
			else:
				return None
		return f
	return dec


def keyvaluesplit(s):
	if '=' not in s:
		raise TypeError('Option must look like option=json_value')
	if s[0] == '_':
		raise ValueError('Option names must not start with `_\'')
	idx = s.index('=')
	o = s[:idx]
	val = json.loads(s[idx + 1:])
	return (o, val)


def parsedotval(s):
	if type(s) is tuple:
		o, val = s
	else:
		o, val = keyvaluesplit(s)

	keys = o.split('.')
	if len(keys) > 1:
		r = (keys[0], {})
		rcur = r[1]
		for key in keys[1:-1]:
			rcur[key] = {}
			rcur = rcur[key]
		rcur[keys[-1]] = val
		return r
	else:
		return (o, val)
