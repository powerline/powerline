# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)


REMOVE_THIS_KEY = object()


def mergeargs(argvalue):
	if not argvalue:
		return None
	r = {}
	for subval in argvalue:
		mergedicts(r, dict([subval]))
	return r


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
