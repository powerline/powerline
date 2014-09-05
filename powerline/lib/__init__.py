# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import json

from functools import wraps


REMOVE_THIS_KEY = object()


def wraps_saveargs(wrapped):
	def dec(wrapper):
		r = wraps(wrapped)(wrapper)
		r.powerline_origin = getattr(wrapped, 'powerline_origin', wrapped)
		return r
	return dec


def mergedicts(d1, d2):
	'''Recursively merge two dictionaries

	First dictionary is modified in-place.
	'''
	for k in d2:
		if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
			mergedicts(d1[k], d2[k])
		elif d2[k] is REMOVE_THIS_KEY:
			d1.pop(k, None)
		else:
			d1[k] = d2[k]


def mergedefaults(d1, d2):
	'''Recursively merge two dictionaries, keeping existing values

	First dictionary is modified in-place.
	'''
	for k in d2:
		if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
			mergedefaults(d1[k], d2[k])
		else:
			d1.setdefault(k, d2[k])


def mergedicts_copy(d1, d2):
	'''Recursively merge two dictionaries.

	Dictionaries are not modified. Copying happens only if necessary. Assumes 
	that first dictionary supports .copy() method.
	'''
	ret = d1.copy()
	for k in d2:
		if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
			ret[k] = mergedicts_copy(d1[k], d2[k])
		else:
			ret[k] = d2[k]
	return ret


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


def keyvaluesplit(s):
	if '=' not in s:
		raise TypeError('Option must look like option=json_value')
	if s[0] == '_':
		raise ValueError('Option names must not start with `_\'')
	idx = s.index('=')
	o = s[:idx]
	rest = s[idx + 1:]
	if not rest:
		val = REMOVE_THIS_KEY
	elif rest[0] in '"{[0193456789' or rest in ('null', 'true', 'false'):
		val = json.loads(s[idx + 1:])
	else:
		val = rest
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
