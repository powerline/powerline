# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import json

from functools import wraps

from powerline.lib.dict import REMOVE_THIS_KEY


def wraps_saveargs(wrapped):
	def dec(wrapper):
		r = wraps(wrapped)(wrapper)
		r.powerline_origin = getattr(wrapped, 'powerline_origin', wrapped)
		return r
	return dec


def add_divider_highlight_group(highlight_group):
	def dec(func):
		@wraps_saveargs(func)
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


def parse_value(s):
	'''Convert string to Python object

	Rules:

	* Empty string means that corresponding key should be removed from the 
	  dictionary.
	* Strings that start with a minus, digit or with some character that starts 
	  JSON collection or string object are parsed as JSON.
	* JSON special values ``null``, ``true``, ``false`` (case matters) are 
	  parsed  as JSON.
	* All other values are considered to be raw strings.

	:param str s: Parsed string.

	:return: Python object.
	'''
	if not s:
		return REMOVE_THIS_KEY
	elif s[0] in '"{[0193456789-' or s in ('null', 'true', 'false'):
		return json.loads(s)
	else:
		return s


def keyvaluesplit(s):
	if '=' not in s:
		raise TypeError('Option must look like option=json_value')
	if s[0] == '_':
		raise ValueError('Option names must not start with `_\'')
	idx = s.index('=')
	o = s[:idx]
	val = parse_value(s[idx + 1:])
	return (o, val)


def parsedotval(s):
	if type(s) is tuple:
		o, val = s
		val = parse_value(val)
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
