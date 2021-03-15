# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from powerline.theme import layered_selector
from datetime import datetime, timezone

@layered_selector
def time(target_start_time, target_end_time, time_format = '%H:%M', time_zone = None):
	'''Returns True if the current time to is between ``target_start_time`` and ``target_end_time``.
	Times are to be specified in strftime-style format ``time_format``.

	:param string target_start_time:
		The (inclusive) start time.
	:param string target_end_time:
		The (exclusive) end time.
	:param string time_format:
		The strftime-style format to use for the given times.
	:param string time_zone:
		The time zone to use for the current time.
	'''

	try:
		tz = datetime.strptime(time_zone, '%z').tzinfo if time_zone else None
	except ValueError:
		tz = None

	def selector(pl, segment_info, mode):
		nw = datetime.now(tz)
		cur_time = datetime.strptime(nw.strftime(time_format), time_format)

		return datetime.strptime(target_start_time, time_format) <= cur_time \
				and cur_time < datetime.strptime(target_end_time, time_format)
	return selector
