# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from math import log


unit_list = tuple(zip(['', 'k', 'M', 'G', 'T', 'P'], [0, 0, 1, 2, 2, 2]))


def humanize_bytes(num, suffix='B', si_prefix=False):
	'''Return a human friendly byte representation.

	Modified version from http://stackoverflow.com/questions/1094841
	'''
	if num == 0:
		return '0 ' + suffix
	div = 1000 if si_prefix else 1024
	exponent = min(int(log(num, div)) if num else 0, len(unit_list) - 1)
	quotient = float(num) / div ** exponent
	unit, decimals = unit_list[exponent]
	if unit and not si_prefix:
		unit = unit.upper() + 'i'
	return ('{{quotient:.{decimals}f}} {{unit}}{{suffix}}'
		.format(decimals=decimals)
		.format(quotient=quotient, unit=unit, suffix=suffix))
