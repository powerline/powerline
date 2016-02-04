# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)


REMOVE_THIS_KEY = object()


def mergeargs(argvalue, remove=False):
	if not argvalue:
		return None
	r = {}
	for subval in argvalue:
		mergedicts(r, dict([subval]), remove=remove)
	return r


def _clear_special_values(d):
	'''Remove REMOVE_THIS_KEY values from dictionary
	'''
	l = [d]
	while l:
		i = l.pop()
		pops = []
		for k, v in i.items():
			if v is REMOVE_THIS_KEY:
				pops.append(k)
			elif isinstance(v, dict):
				l.append(v)
		for k in pops:
			i.pop(k)


def mergedicts(d1, d2, remove=True):
	'''Recursively merge two dictionaries

	First dictionary is modified in-place.
	'''
	_setmerged(d1, d2)
	for k in d2:
		if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
			mergedicts(d1[k], d2[k], remove)
		elif remove and d2[k] is REMOVE_THIS_KEY:
			d1.pop(k, None)
		else:
			if remove and isinstance(d2[k], dict):
				_clear_special_values(d2[k])
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


def _setmerged(d1, d2):
	if hasattr(d1, 'setmerged'):
		d1.setmerged(d2)


def mergedicts_copy(d1, d2):
	'''Recursively merge two dictionaries.

	Dictionaries are not modified. Copying happens only if necessary. Assumes 
	that first dictionary supports .copy() method.
	'''
	ret = d1.copy()
	_setmerged(ret, d2)
	for k in d2:
		if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
			ret[k] = mergedicts_copy(d1[k], d2[k])
		else:
			ret[k] = d2[k]
	return ret


def updated(d, *args, **kwargs):
    '''Copy dictionary and update it with provided arguments
    '''
    d = d.copy()
    d.update(*args, **kwargs)
    return d
