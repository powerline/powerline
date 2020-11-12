# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from datetime import datetime


def date(pl, format='%Y-%m-%d', istime=False, timezone=None):
	'''Return the current date.

	:param str format:
		strftime-style date format string
	:param bool istime:
		If true then segment uses ``time`` highlight group.
	:param string timezone:
		Specify a timezone to use as ``+HHMM`` or ``-HHMM``.
		(Defaults to system defaults.)

	Divider highlight group used: ``time:divider``.

	Highlight groups used: ``time`` or ``date``.
	'''

	try:
		tz = datetime.strptime(timezone, '%z').tzinfo if timezone else None
	except ValueError:
		tz = None

	nw = datetime.now(tz)

	try:
		contents = nw.strftime(format)
	except UnicodeEncodeError:
		contents = nw.strftime(format.encode('utf-8')).decode('utf-8')

	return [{
		'contents': contents,
		'highlight_groups': (['time'] if istime else []) + ['date'],
		'divider_highlight_group': 'time:divider' if istime else None,
	}]


UNICODE_TEXT_TRANSLATION = {
	ord('\''): '’',
	ord('-'): '‐',
}


def fuzzy_time(pl, format='{minute_str} {hour_str}', unicode_text=False, timezone=None, hour_str=['twelve', 'one', 'two', 'three', 'four',
    'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven'], minute_str = {
	'0':  'o\'clock', '5':  'five past', '10': 'ten past','15': 'quarter past',
	'20': 'twenty past', '25': 'twenty-five past', '30': 'half past', '35': 'twenty-five to',
	'40': 'twenty to', '45': 'quarter to', '50': 'ten to', '55': 'five to'
	}, special_case_str = {
	    '(23, 58)': 'round about midnight',
	    '(23, 59)': 'round about midnight',
	    '(0, 0)': 'midnight',
	    '(0, 1)': 'round about midnight',
	    '(0, 2)': 'round about midnight',
	    '(12, 0)': 'noon',
	}):

	'''Display the current time as fuzzy time, e.g. "quarter past six".

	:param string format:
		Format used to display the fuzzy time. (Ignored when a special time
		is displayed.)
	:param bool unicode_text:
		If true then hyphenminuses (regular ASCII ``-``) and single quotes are
		replaced with unicode dashes and apostrophes.
	:param string timezone:
		Specify a timezone to use as ``+HHMM`` or ``-HHMM``.
		(Defaults to system defaults.)
	:param string list hour_str:
		Strings to be used to display the hour, starting with midnight.
		(This list may contain 12 or 24 entries.)
	:param dict minute_str:
		Dictionary mapping minutes to strings to be used to display them.
	:param dict special_case_str:
		Special strings for special times.

	Highlight groups used: ``fuzzy_time``.
	'''

	try:
		tz = datetime.strptime(timezone, '%z').tzinfo if timezone else None
	except ValueError:
		tz = None

	now = datetime.now(tz)

	try:
		# We don't want to enforce a special type of spaces/ alignment in the input
		from ast import literal_eval
		special_case_str = {literal_eval(x):special_case_str[x] for x in special_case_str}
		result = special_case_str[(now.hour, now.minute)]
		if unicode_text:
			result = result.translate(UNICODE_TEXT_TRANSLATION)
		return result
	except KeyError:
		pass

	hour = now.hour
	if now.minute >= 30:
		hour = hour + 1
	hour = hour % len(hour_str)

	min_dis = 100
	min_pos = 0

	for mn in minute_str:
		mn = int(mn)
		if now.minute >= mn and now.minute - mn < min_dis:
			min_dis = now.minute - mn
			min_pos = mn
		elif now.minute < mn and mn - now.minute < min_dis:
			min_dis = mn - now.minute
			min_pos = mn
	result = format.format(minute_str=minute_str[str(min_pos)], hour_str=hour_str[hour])

	if unicode_text:
		result = result.translate(UNICODE_TEXT_TRANSLATION)

	return result
