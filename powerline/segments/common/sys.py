# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from multiprocessing import cpu_count as _cpu_count

from powerline.lib.threaded import ThreadedSegment
from powerline.lib import add_divider_highlight_group
from powerline.segments import with_docstring


cpu_count = None


def system_load(pl, format='{avg:.1f}', threshold_good=1, threshold_bad=2,
                track_cpu_count=False, short=False):
	'''Return system load average.

	Highlights using ``system_load_good``, ``system_load_bad`` and
	``system_load_ugly`` highlighting groups, depending on the thresholds
	passed to the function.

	:param str format:
		format string, receives ``avg`` as an argument
	:param float threshold_good:
		threshold for gradient level 0: any normalized load average below this
		value will have this gradient level.
	:param float threshold_bad:
		threshold for gradient level 100: any normalized load average above this
		value will have this gradient level. Load averages between
		``threshold_good`` and ``threshold_bad`` receive gradient level that
		indicates relative position in this interval:
		(``100 * (cur-good) / (bad-good)``).
		Note: both parameters are checked against normalized load averages.
	:param bool track_cpu_count:
		if True powerline will continuously poll the system to detect changes
		in the number of CPUs.
	:param bool short:
		if True only the sys load over last 1 minute will be displayed.

	Divider highlight group used: ``background:divider``.

	Highlight groups used: ``system_load_gradient`` (gradient) or ``system_load``.
	'''
	global cpu_count
	try:
		cpu_num = cpu_count = _cpu_count() if cpu_count is None or track_cpu_count else cpu_count
	except NotImplementedError:
		pl.warn('Unable to get CPU count: method is not implemented')
		return None
	ret = []
	for avg in os.getloadavg():
		normalized = avg / cpu_num
		if normalized < threshold_good:
			gradient_level = 0
		elif normalized < threshold_bad:
			gradient_level = (normalized - threshold_good) * 100.0 / (threshold_bad - threshold_good)
		else:
			gradient_level = 100
		ret.append({
			'contents': format.format(avg=avg),
			'highlight_groups': ['system_load_gradient', 'system_load'],
			'divider_highlight_group': 'background:divider',
			'gradient_level': gradient_level,
		})

		if short:
		    return ret

	ret[0]['contents'] += ' '
	ret[1]['contents'] += ' '
	return ret


try:
	import psutil

	class CPULoadPercentSegment(ThreadedSegment):
		interval = 1

		def update(self, old_cpu):
			return psutil.cpu_percent(interval=None)

		def run(self):
			while not self.shutdown_event.is_set():
				try:
					self.update_value = psutil.cpu_percent(interval=self.interval)
				except Exception as e:
					self.exception('Exception while calculating cpu_percent: {0}', str(e))

		def render(self, cpu_percent, format='{0:.0f}%', **kwargs):
			if not cpu_percent:
				return None
			return [{
				'contents': format.format(cpu_percent),
				'gradient_level': cpu_percent,
				'highlight_groups': ['cpu_load_percent_gradient', 'cpu_load_percent'],
			}]
except ImportError:
	class CPULoadPercentSegment(ThreadedSegment):
		interval = 1

		@staticmethod
		def startup(**kwargs):
			pass

		@staticmethod
		def start():
			pass

		@staticmethod
		def shutdown():
			pass

		@staticmethod
		def render(cpu_percent, pl, format='{0:.0f}%', **kwargs):
			pl.warn('Module “psutil” is not installed, thus CPU load is not available')
			return None


cpu_load_percent = with_docstring(CPULoadPercentSegment(),
'''Return the average CPU load as a percentage.

Requires the ``psutil`` module.

:param str format:
	Output format. Accepts measured CPU load as the first argument.

Highlight groups used: ``cpu_load_percent_gradient`` (gradient) or ``cpu_load_percent``.
''')


if os.path.exists('/proc/uptime'):
	def _get_uptime():
		with open('/proc/uptime', 'r') as f:
			return int(float(f.readline().split()[0]))
elif 'psutil' in globals():
	from time import time

	if hasattr(psutil, 'boot_time'):
		def _get_uptime():
			return int(time() - psutil.boot_time())
	else:
		def _get_uptime():
			return int(time() - psutil.BOOT_TIME)
else:
	def _get_uptime():
		raise NotImplementedError


@add_divider_highlight_group('background:divider')
def uptime(pl, days_format='{days:d}d', hours_format=' {hours:d}h', minutes_format=' {minutes:d}m', seconds_format=' {seconds:d}s', shorten_len=3):
	'''Return system uptime.

	:param str days_format:
		day format string, will be passed ``days`` as the argument
	:param str hours_format:
		hour format string, will be passed ``hours`` as the argument
	:param str minutes_format:
		minute format string, will be passed ``minutes`` as the argument
	:param str seconds_format:
		second format string, will be passed ``seconds`` as the argument
	:param int shorten_len:
		shorten the amount of units (days, hours, etc.) displayed

	Divider highlight group used: ``background:divider``.
	'''
	try:
		seconds = _get_uptime()
	except NotImplementedError:
		pl.warn('Unable to get uptime. You should install psutil module')
		return None
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	time_formatted = list(filter(None, [
		days_format.format(days=days) if days and days_format else None,
		hours_format.format(hours=hours) if hours and hours_format else None,
		minutes_format.format(minutes=minutes) if minutes and minutes_format else None,
		seconds_format.format(seconds=seconds) if seconds and seconds_format else None,
	]))[0:shorten_len]
	return ''.join(time_formatted).strip()
