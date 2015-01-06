# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from datetime import datetime


def date(pl, format='%Y-%m-%d', istime=False):
	'''Return the current date.

	:param str format:
		strftime-style date format string
	:param bool istime:
		If true then segment uses ``time`` highlight group.

	Divider highlight group used: ``time:divider``.

	Highlight groups used: ``time`` or ``date``.
	'''
	return [{
		'contents': datetime.now().strftime(format),
		'highlight_groups': (['time'] if istime else []) + ['date'],
		'divider_highlight_group': 'time:divider' if istime else None,
	}]


UNICODE_TEXT_TRANSLATION = {
	ord('\''): '’',
	ord('-'): '‐',
}


def fuzzy_time(pl, unicode_text=False):
	'''Display the current time as fuzzy time, e.g. "quarter past six".

	:param bool unicode_text:
		If true then hyphenminuses (regular ASCII ``-``) and single quotes are 
		replaced with unicode dashes and apostrophes.
	'''
	hour_str = ['twelve', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven']
	minute_str = {
		5: 'five past',
		10: 'ten past',
		15: 'quarter past',
		20: 'twenty past',
		25: 'twenty-five past',
		30: 'half past',
		35: 'twenty-five to',
		40: 'twenty to',
		45: 'quarter to',
		50: 'ten to',
		55: 'five to',
	}
	special_case_str = {
		(23, 58): 'round about midnight',
		(23, 59): 'round about midnight',
		(0, 0): 'midnight',
		(0, 1): 'round about midnight',
		(0, 2): 'round about midnight',
		(12, 0): 'noon',
	}

	now = datetime.now()

	try:
		return special_case_str[(now.hour, now.minute)]
	except KeyError:
		pass

	hour = now.hour
	if now.minute > 32:
		if hour == 23:
			hour = 0
		else:
			hour += 1
	if hour > 11:
		hour = hour - 12
	hour = hour_str[hour]

	minute = int(round(now.minute / 5.0) * 5)
	if minute == 60 or minute == 0:
		result = ' '.join([hour, 'o\'clock'])
	else:
		minute = minute_str[minute]
		result = ' '.join([minute, hour])

	if unicode_text:
		result = result.translate(UNICODE_TEXT_TRANSLATION)

	return result
