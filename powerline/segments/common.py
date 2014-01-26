# vim:fileencoding=utf-8:noet

from __future__ import unicode_literals, absolute_import

import os
import sys

from datetime import datetime
import socket
from multiprocessing import cpu_count as _cpu_count

from powerline.lib import add_divider_highlight_group
from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.vcs import guess, tree_status
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment, with_docstring
from powerline.lib.monotonic import monotonic
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.theme import requires_segment_info
from collections import namedtuple


cpu_count = None


@requires_segment_info
def environment(pl, segment_info, variable=None):
	'''Return the value of any defined environment variable

	:param string variable:
		The environment variable to return if found
	'''
	return segment_info['environ'].get(variable, None)


@requires_segment_info
def hostname(pl, segment_info, only_if_ssh=False, exclude_domain=False):
	'''Return the current hostname.

	:param bool only_if_ssh:
		only return the hostname if currently in an SSH session
	:param bool exclude_domain:
		return the hostname without domain if there is one
	'''
	if only_if_ssh and not segment_info['environ'].get('SSH_CLIENT'):
		return None
	if exclude_domain:
		return socket.gethostname().split('.')[0]
	return socket.gethostname()


@requires_segment_info
def branch(pl, segment_info, status_colors=False):
	'''Return the current VCS branch.

	:param bool status_colors:
		determines whether repository status will be used to determine highlighting. Default: False.

	Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.
	'''
	name = segment_info['getcwd']()
	repo = guess(path=name)
	if repo is not None:
		branch = repo.branch()
		scol = ['branch']
		if status_colors:
			status = tree_status(repo, pl)
			scol.insert(0, 'branch_dirty' if status and status.strip() else 'branch_clean')
		return [{
			'contents': branch,
			'highlight_group': scol,
		}]


@requires_segment_info
def cwd(pl, segment_info, dir_shorten_len=None, dir_limit_depth=None, use_path_separator=False):
	'''Return the current working directory.

	Returns a segment list to create a breadcrumb-like effect.

	:param int dir_shorten_len:
		shorten parent directory names to this length (e.g. :file:`/long/path/to/powerline` → :file:`/l/p/t/powerline`)
	:param int dir_limit_depth:
		limit directory depth to this number (e.g. :file:`/long/path/to/powerline` → :file:`⋯/to/powerline`)
	:param bool use_path_separator:
		Use path separator in place of soft divider.

	Divider highlight group used: ``cwd:divider``.

	Highlight groups used: ``cwd:current_folder`` or ``cwd``. It is recommended to define all highlight groups.
	'''
	import re
	try:
		cwd = segment_info['getcwd']()
	except OSError as e:
		if e.errno == 2:
			# user most probably deleted the directory
			# this happens when removing files from Mercurial repos for example
			pl.warn('Current directory not found')
			cwd = "[not found]"
		else:
			raise
	home = segment_info['home']
	if home:
		cwd = re.sub('^' + re.escape(home), '~', cwd, 1)
	cwd_split = cwd.split(os.sep)
	cwd_split_len = len(cwd_split)
	cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
	if dir_limit_depth and cwd_split_len > dir_limit_depth + 1:
		del(cwd[0:-dir_limit_depth])
		cwd.insert(0, '⋯')
	ret = []
	if not cwd[0]:
		cwd[0] = '/'
	draw_inner_divider = not use_path_separator
	for part in cwd:
		if not part:
			continue
		if use_path_separator:
			part += os.sep
		ret.append({
			'contents': part,
			'divider_highlight_group': 'cwd:divider',
			'draw_inner_divider': draw_inner_divider,
		})
	ret[-1]['highlight_group'] = ['cwd:current_folder', 'cwd']
	if use_path_separator:
		ret[-1]['contents'] = ret[-1]['contents'][:-1]
		if len(ret) > 1 and ret[0]['contents'][0] == os.sep:
			ret[0]['contents'] = ret[0]['contents'][1:]
	return ret


def date(pl, format='%Y-%m-%d', istime=False):
	'''Return the current date.

	:param str format:
		strftime-style date format string

	Divider highlight group used: ``time:divider``.

	Highlight groups used: ``time`` or ``date``.
	'''
	return [{
		'contents': datetime.now().strftime(format),
		'highlight_group': (['time'] if istime else []) + ['date'],
		'divider_highlight_group': 'time:divider' if istime else None,
	}]


def fuzzy_time(pl):
	'''Display the current time as fuzzy time, e.g. "quarter past six".'''
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
		return ' '.join([hour, 'o\'clock'])
	else:
		minute = minute_str[minute]
		return ' '.join([minute, hour])


def _external_ip(query_url='http://ipv4.icanhazip.com/'):
	return urllib_read(query_url).strip()


class ExternalIpSegment(ThreadedSegment):
	interval = 300

	def set_state(self, query_url='http://ipv4.icanhazip.com/', **kwargs):
		self.query_url = query_url
		super(ExternalIpSegment, self).set_state(**kwargs)

	def update(self, old_ip):
		return _external_ip(query_url=self.query_url)

	def render(self, ip, **kwargs):
		if not ip:
			return None
		return [{'contents': ip, 'divider_highlight_group': 'background:divider'}]


external_ip = with_docstring(ExternalIpSegment(),
'''Return external IP address.

Suggested URIs:

* http://ipv4.icanhazip.com/
* http://ipv6.icanhazip.com/
* http://icanhazip.com/ (returns IPv6 address if available, else IPv4)

:param str query_url:
	URI to query for IP address, should return only the IP address as a text string

Divider highlight group used: ``background:divider``.
''')


# Weather condition code descriptions available at
# http://developer.yahoo.com/weather/#codes
weather_conditions_codes = (
	('tornado',                 'stormy'),  # 0
	('tropical_storm',          'stormy'),  # 1
	('hurricane',               'stormy'),  # 2
	('severe_thunderstorms',    'stormy'),  # 3
	('thunderstorms',           'stormy'),  # 4
	('mixed_rain_and_snow',     'rainy' ),  # 5
	('mixed_rain_and_sleet',    'rainy' ),  # 6
	('mixed_snow_and_sleet',    'snowy' ),  # 7
	('freezing_drizzle',        'rainy' ),  # 8
	('drizzle',                 'rainy' ),  # 9
	('freezing_rain',           'rainy' ),  # 10
	('showers',                 'rainy' ),  # 11
	('showers',                 'rainy' ),  # 12
	('snow_flurries',           'snowy' ),  # 13
	('light_snow_showers',      'snowy' ),  # 14
	('blowing_snow',            'snowy' ),  # 15
	('snow',                    'snowy' ),  # 16
	('hail',                    'snowy' ),  # 17
	('sleet',                   'snowy' ),  # 18
	('dust',                    'foggy' ),  # 19
	('fog',                     'foggy' ),  # 20
	('haze',                    'foggy' ),  # 21
	('smoky',                   'foggy' ),  # 22
	('blustery',                'foggy' ),  # 23
	('windy',                           ),  # 24
	('cold',                    'day'   ),  # 25
	('clouds',                  'cloudy'),  # 26
	('mostly_cloudy_night',     'cloudy'),  # 27
	('mostly_cloudy_day',       'cloudy'),  # 28
	('partly_cloudy_night',     'cloudy'),  # 29
	('partly_cloudy_day',       'cloudy'),  # 30
	('clear_night',             'night' ),  # 31
	('sun',                     'sunny' ),  # 32
	('fair_night',              'night' ),  # 33
	('fair_day',                'day'   ),  # 34
	('mixed_rain_and_hail',     'rainy' ),  # 35
	('hot',                     'sunny' ),  # 36
	('isolated_thunderstorms',  'stormy'),  # 37
	('scattered_thunderstorms', 'stormy'),  # 38
	('scattered_thunderstorms', 'stormy'),  # 39
	('scattered_showers',       'rainy' ),  # 40
	('heavy_snow',              'snowy' ),  # 41
	('scattered_snow_showers',  'snowy' ),  # 42
	('heavy_snow',              'snowy' ),  # 43
	('partly_cloudy',           'cloudy'),  # 44
	('thundershowers',          'rainy' ),  # 45
	('snow_showers',            'snowy' ),  # 46
	('isolated_thundershowers', 'rainy' ),  # 47
)
# ('day',    (25, 34)),
# ('rainy',  (5, 6, 8, 9, 10, 11, 12, 35, 40, 45, 47)),
# ('cloudy', (26, 27, 28, 29, 30, 44)),
# ('snowy',  (7, 13, 14, 15, 16, 17, 18, 41, 42, 43, 46)),
# ('stormy', (0, 1, 2, 3, 4, 37, 38, 39)),
# ('foggy',  (19, 20, 21, 22, 23)),
# ('sunny',  (32, 36)),
# ('night',  (31, 33))):
weather_conditions_icons = {
	'day':           '〇',
	'blustery':      '⚑',
	'rainy':         '☔',
	'cloudy':        '☁',
	'snowy':         '❅',
	'stormy':        '☈',
	'foggy':         '〰',
	'sunny':         '☼',
	'night':         '☾',
	'windy':         '☴',
	'not_available': '�',
	'unknown':       '⚠',
}

temp_conversions = {
	'C': lambda temp: temp,
	'F': lambda temp: (temp * 9 / 5) + 32,
	'K': lambda temp: temp + 273.15,
}

# Note: there are also unicode characters for units: ℃, ℉ and  K
temp_units = {
	'C': '°C',
	'F': '°F',
	'K': 'K',
}


class WeatherSegment(ThreadedSegment):
	interval = 600

	def set_state(self, location_query=None, **kwargs):
		self.location = location_query
		self.url = None
		super(WeatherSegment, self).set_state(**kwargs)

	def update(self, old_weather):
		import json

		if not self.url:
			# Do not lock attribute assignments in this branch: they are used 
			# only in .update()
			if not self.location:
				location_data = json.loads(urllib_read('http://freegeoip.net/json/'))
				self.location = ','.join([location_data['city'],
											location_data['region_code'],
											location_data['country_code']])
			query_data = {
				'q':
				'use "http://github.com/yql/yql-tables/raw/master/weather/weather.bylocation.xml" as we;'
				'select * from we where location="{0}" and unit="c"'.format(self.location).encode('utf-8'),
				'format': 'json',
			}
			self.url = 'http://query.yahooapis.com/v1/public/yql?' + urllib_urlencode(query_data)

		raw_response = urllib_read(self.url)
		if not raw_response:
			self.error('Failed to get response')
			return
		response = json.loads(raw_response)
		condition = response['query']['results']['weather']['rss']['channel']['item']['condition']
		condition_code = int(condition['code'])
		temp = float(condition['temp'])

		try:
			icon_names = weather_conditions_codes[condition_code]
		except IndexError:
			if condition_code == 3200:
				icon_names = ('not_available',)
				self.warn('Weather is not available for location {0}', self.location)
			else:
				icon_names = ('unknown',)
				self.error('Unknown condition code: {0}', condition_code)

		return (temp, icon_names)

	def render(self, weather, icons=None, unit='C', temp_format=None, temp_coldest=-30, temp_hottest=40, **kwargs):
		if not weather:
			return None

		temp, icon_names = weather

		for icon_name in icon_names:
			if icons:
				if icon_name in icons:
					icon = icons[icon_name]
					break
		else:
			icon = weather_conditions_icons[icon_names[-1]]

		temp_format = temp_format or ('{temp:.0f}' + temp_units[unit])
		converted_temp = temp_conversions[unit](temp)
		if temp <= temp_coldest:
			gradient_level = 0
		elif temp >= temp_hottest:
			gradient_level = 100
		else:
			gradient_level = (temp - temp_coldest) * 100.0 / (temp_hottest - temp_coldest)
		groups = ['weather_condition_' + icon_name for icon_name in icon_names] + ['weather_conditions', 'weather']
		return [
			{
				'contents': icon + ' ',
				'highlight_group': groups,
				'divider_highlight_group': 'background:divider',
			},
			{
				'contents': temp_format.format(temp=converted_temp),
				'highlight_group': ['weather_temp_gradient', 'weather_temp', 'weather'],
				'divider_highlight_group': 'background:divider',
				'gradient_level': gradient_level,
			},
		]


weather = with_docstring(WeatherSegment(),
'''Return weather from Yahoo! Weather.

Uses GeoIP lookup from http://freegeoip.net/ to automatically determine
your current location. This should be changed if you're in a VPN or if your
IP address is registered at another location.

Returns a list of colorized icon and temperature segments depending on
weather conditions.

:param str unit:
	temperature unit, can be one of ``F``, ``C`` or ``K``
:param str location_query:
	location query for your current location, e.g. ``oslo, norway``
:param dict icons:
	dict for overriding default icons, e.g. ``{'heavy_snow' : u'❆'}``
:param str temp_format:
	format string, receives ``temp`` as an argument. Should also hold unit.
:param float temp_coldest:
	coldest temperature. Any temperature below it will have gradient level equal 
	to zero.
:param float temp_hottest:
	hottest temperature. Any temperature above it will have gradient level equal 
	to 100. Temperatures between ``temp_coldest`` and ``temp_hottest`` receive 
	gradient level that indicates relative position in this interval 
	(``100 * (cur-coldest) / (hottest-coldest)``).

Divider highlight group used: ``background:divider``.

Highlight groups used: ``weather_conditions`` or ``weather``, ``weather_temp_gradient`` (gradient) or ``weather``.
Also uses ``weather_conditions_{condition}`` for all weather conditions supported by Yahoo.
''')


def system_load(pl, format='{avg:.1f}', threshold_good=1, threshold_bad=2, track_cpu_count=False):
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
			'highlight_group': ['system_load_gradient', 'system_load'],
			'divider_highlight_group': 'background:divider',
			'gradient_level': gradient_level,
		})
	ret[0]['contents'] += ' '
	ret[1]['contents'] += ' '
	return ret


try:
	import psutil

	def _get_bytes(interface):
		try:
			io_counters = psutil.net_io_counters(pernic=True)
		except AttributeError:
			io_counters = psutil.network_io_counters(pernic=True)
		if_io = io_counters.get(interface)
		if not if_io:
			return None
		return if_io.bytes_recv, if_io.bytes_sent

	def _get_interfaces():
		io_counters = psutil.network_io_counters(pernic=True)
		for interface, data in io_counters.items():
			if data:
				yield interface, data.bytes_recv, data.bytes_sent

	def _get_user(segment_info):
		return psutil.Process(os.getpid()).username

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
				'highlight_group': ['cpu_load_percent_gradient', 'cpu_load_percent'],
			}]
except ImportError:
	def _get_bytes(interface):  # NOQA
		with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
			rx = int(file_obj.read())
		with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
			tx = int(file_obj.read())
		return (rx, tx)

	def _get_interfaces():  # NOQA
		for interface in os.listdir('/sys/class/net'):
			x = _get_bytes(interface)
			if x is not None:
				yield interface, x[0], x[1]

	def _get_user(segment_info):  # NOQA
		return segment_info['environ'].get('USER', None)

	class CPULoadPercentSegment(ThreadedSegment):  # NOQA
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
			pl.warn('psutil package is not installed, thus CPU load is not available')
			return None


cpu_load_percent = with_docstring(CPULoadPercentSegment(),
'''Return the average CPU load as a percentage.

Requires the ``psutil`` module.

:param str format:
	Output format. Accepts measured CPU load as the first argument.

Highlight groups used: ``cpu_load_percent_gradient`` (gradient) or ``cpu_load_percent``.
''')


username = False
# os.geteuid is not available on windows
_geteuid = getattr(os, 'geteuid', lambda: 1)


def user(pl, segment_info=None, hide_user=None):
	'''Return the current user.

	:param str hide_user:
		Omit showing segment for users with names equal to this string.

	Highlights the user with the ``superuser`` if the effective user ID is 0.

	Highlight groups used: ``superuser`` or ``user``. It is recommended to define all highlight groups.
	'''
	global username
	if username is False:
		username = _get_user(segment_info)
	if username is None:
		pl.warn('Failed to get username')
		return None
	if username == hide_user:
		return None
	euid = _geteuid()
	return [{
		'contents': username,
		'highlight_group': 'user' if euid != 0 else ['superuser', 'user'],
	}]
if 'psutil' not in globals():
	user = requires_segment_info(user)


if os.path.exists('/proc/uptime'):
	def _get_uptime():
		with open('/proc/uptime', 'r') as f:
			return int(float(f.readline().split()[0]))
elif 'psutil' in globals():
	from time import time

	def _get_uptime():  # NOQA
		# psutil.BOOT_TIME is not subject to clock adjustments, but time() is. 
		# Thus it is a fallback to /proc/uptime reading and not the reverse.
		return int(time() - psutil.BOOT_TIME)
else:
	def _get_uptime():  # NOQA
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
		pl.warn('Unable to get uptime. You should install psutil package')
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


class NetworkLoadSegment(KwThreadedSegment):
	import re
	interfaces = {}
	replace_num_pat = re.compile(r'[a-zA-Z]+')

	@staticmethod
	def key(interface='detect', **kwargs):
		return interface

	def compute_state(self, interface):
		if interface == 'detect':
			proc_exists = getattr(self, 'proc_exists', None)
			if proc_exists is None:
				proc_exists = self.proc_exists = os.path.exists('/proc/net/route')
			if proc_exists:
				# Look for default interface in routing table
				with open('/proc/net/route', 'rb') as f:
					for line in f.readlines():
						parts = line.split()
						if len(parts) > 1:
							iface, destination = parts[:2]
							if not destination.replace(b'0', b''):
								interface = iface.decode('utf-8')
								break
			if interface == 'detect':
				# Choose interface with most total activity, excluding some
				# well known interface names
				interface, total = 'eth0', -1
				for name, rx, tx in _get_interfaces():
					base = self.replace_num_pat.match(name)
					if None in (base, rx, tx) or base.group() in ('lo', 'vmnet', 'sit'):
						continue
					activity = rx + tx
					if activity > total:
						total = activity
						interface = name

		try:
			idata = self.interfaces[interface]
			try:
				idata['prev'] = idata['last']
			except KeyError:
				pass
		except KeyError:
			idata = {}
			if self.run_once:
				idata['prev'] = (monotonic(), _get_bytes(interface))
				self.shutdown_event.wait(self.interval)
			self.interfaces[interface] = idata

		idata['last'] = (monotonic(), _get_bytes(interface))
		return idata.copy()

	def render_one(self, idata, recv_format='⬇ {value:>8}', sent_format='⬆ {value:>8}', suffix='B/s', si_prefix=False, **kwargs):
		if not idata or 'prev' not in idata:
			return None

		t1, b1 = idata['prev']
		t2, b2 = idata['last']
		measure_interval = t2 - t1

		if None in (b1, b2):
			return None

		r = []
		for i, key in zip((0, 1), ('recv', 'sent')):
			format = locals()[key + '_format']
			try:
				value = (b2[i] - b1[i]) / measure_interval
			except ZeroDivisionError:
				self.warn('Measure interval zero.')
				value = 0
			max_key = key + '_max'
			is_gradient = max_key in kwargs
			hl_groups = ['network_load_' + key, 'network_load']
			if is_gradient:
				hl_groups[:0] = (group + '_gradient' for group in hl_groups)
			r.append({
				'contents': format.format(value=humanize_bytes(value, suffix, si_prefix)),
				'divider_highlight_group': 'background:divider',
				'highlight_group': hl_groups,
			})
			if is_gradient:
				max = kwargs[max_key]
				if value >= max:
					r[-1]['gradient_level'] = 100
				else:
					r[-1]['gradient_level'] = value * 100.0 / max

		return r


network_load = with_docstring(NetworkLoadSegment(),
'''Return the network load.

Uses the ``psutil`` module if available for multi-platform compatibility,
falls back to reading
:file:`/sys/class/net/{interface}/statistics/{rx,tx}_bytes`.

:param str interface:
	network interface to measure (use the special value "detect" to have powerline try to auto-detect the network interface)
:param str suffix:
	string appended to each load string
:param bool si_prefix:
	use SI prefix, e.g. MB instead of MiB
:param str recv_format:
	format string, receives ``value`` as argument
:param str sent_format:
	format string, receives ``value`` as argument
:param float recv_max:
	maximum number of received bytes per second. Is only used to compute 
	gradient level
:param float sent_max:
	maximum number of sent bytes per second. Is only used to compute gradient 
	level

Divider highlight group used: ``background:divider``.

Highlight groups used: ``network_load_sent_gradient`` (gradient) or ``network_load_recv_gradient`` (gradient) or ``network_load_gradient`` (gradient), ``network_load_sent`` or ``network_load_recv`` or ``network_load``.
''')


@requires_segment_info
def virtualenv(pl, segment_info):
	'''Return the name of the current Python virtualenv.'''
	return os.path.basename(segment_info['environ'].get('VIRTUAL_ENV', '')) or None


_IMAPKey = namedtuple('Key', 'username password server port folder')


class EmailIMAPSegment(KwThreadedSegment):
	interval = 60

	@staticmethod
	def key(username, password, server='imap.gmail.com', port=993, folder='INBOX', **kwargs):
		return _IMAPKey(username, password, server, port, folder)

	def compute_state(self, key):
		if not key.username or not key.password:
			self.warn('Username and password are not configured')
			return None
		try:
			import imaplib
			import re
			mail = imaplib.IMAP4_SSL(key.server, key.port)
			mail.login(key.username, key.password)
			rc, message = mail.status(key.folder, '(UNSEEN)')
			unread_str = message[0].decode('utf-8')
			unread_count = int(re.search('UNSEEN (\d+)', unread_str).group(1))
		except imaplib.IMAP4.error as e:
			unread_count = str(e)
		return unread_count

	@staticmethod
	def render_one(unread_count, max_msgs=None, **kwargs):
		if not unread_count:
			return None
		elif type(unread_count) != int or not max_msgs:
			return [{
				'contents': str(unread_count),
				'highlight_group': 'email_alert',
			}]
		else:
			return [{
				'contents': str(unread_count),
				'highlight_group': ['email_alert_gradient', 'email_alert'],
				'gradient_level': min(unread_count * 100.0 / max_msgs, 100),
			}]


email_imap_alert = with_docstring(EmailIMAPSegment(),
'''Return unread e-mail count for IMAP servers.

:param str username:
	login username
:param str password:
	login password
:param str server:
	e-mail server
:param int port:
	e-mail server port
:param str folder:
	folder to check for e-mails
:param int max_msgs:
	Maximum number of messages. If there are more messages then max_msgs then it 
	will use gradient level equal to 100, otherwise gradient level is equal to 
	``100 * msgs_num / max_msgs``. If not present gradient is not computed.

Highlight groups used: ``email_alert_gradient`` (gradient), ``email_alert``.
''')


class NowPlayingSegment(object):
	STATE_SYMBOLS = {
		'fallback': '♫',
		'play': '▶',
		'pause': '▮▮',
		'stop': '■',
	}

	def __call__(self, player='mpd', format='{state_symbol} {artist} - {title} ({total})', **kwargs):
		player_func = getattr(self, 'player_{0}'.format(player))
		stats = {
			'state': None,
			'state_symbol': self.STATE_SYMBOLS['fallback'],
			'album': None,
			'artist': None,
			'title': None,
			'elapsed': None,
			'total': None,
		}
		func_stats = player_func(**kwargs)
		if not func_stats:
			return None
		stats.update(func_stats)
		return format.format(**stats)

	@staticmethod
	def _run_cmd(cmd):
		from subprocess import Popen, PIPE
		try:
			p = Popen(cmd, stdout=PIPE)
			stdout, err = p.communicate()
		except OSError as e:
			sys.stderr.write('Could not execute command ({0}): {1}\n'.format(e, cmd))
			return None
		return stdout.strip()

	@staticmethod
	def _convert_state(state):
		state = state.lower()
		if 'play' in state:
			return 'play'
		if 'pause' in state:
			return 'pause'
		if 'stop' in state:
			return 'stop'

	@staticmethod
	def _convert_seconds(seconds):
		return '{0:.0f}:{1:02.0f}'.format(*divmod(float(seconds), 60))

	def player_cmus(self, pl):
		'''Return cmus player information.

		cmus-remote -Q returns data with multi-level information i.e.
			status playing
			file <file_name>
			tag artist <artist_name>
			tag title <track_title>
			tag ..
			tag n
			set continue <true|false>
			set repeat <true|false>
			set ..
			set n

		For the information we are looking for we don't really care if we're on
		the tag level or the set level. The dictionary comprehension in this
		method takes anything in ignore_levels and brings the key inside that
		to the first level of the dictionary.
		'''
		now_playing_str = self._run_cmd(['cmus-remote', '-Q'])
		if not now_playing_str:
			return
		ignore_levels = ('tag', 'set',)
		now_playing = dict(((token[0] if token[0] not in ignore_levels else token[1],
			(' '.join(token[1:]) if token[0] not in ignore_levels else
			' '.join(token[2:]))) for token in [line.split(' ') for line in now_playing_str.split('\n')[:-1]]))
		state = self._convert_state(now_playing.get('status'))
		return {
			'state': state,
			'state_symbol': self.STATE_SYMBOLS.get(state),
			'album': now_playing.get('album'),
			'artist': now_playing.get('artist'),
			'title': now_playing.get('title'),
			'elapsed': self._convert_seconds(now_playing.get('position', 0)),
			'total': self._convert_seconds(now_playing.get('duration', 0)),
		}

	def player_mpd(self, pl, host='localhost', port=6600):
		try:
			import mpd
			client = mpd.MPDClient()
			client.connect(host, port)
			now_playing = client.currentsong()
			if not now_playing:
				return
			status = client.status()
			client.close()
			client.disconnect()
			return {
				'state': status.get('state'),
				'state_symbol': self.STATE_SYMBOLS.get(status.get('state')),
				'album': now_playing.get('album'),
				'artist': now_playing.get('artist'),
				'title': now_playing.get('title'),
				'elapsed': self._convert_seconds(now_playing.get('elapsed', 0)),
				'total': self._convert_seconds(now_playing.get('time', 0)),
			}
		except ImportError:
			now_playing = self._run_cmd(['mpc', 'current', '-f', '%album%\n%artist%\n%title%\n%time%', '-h', str(host), '-p', str(port)])
			if not now_playing:
				return
			now_playing = now_playing.split('\n')
			return {
				'album': now_playing[0],
				'artist': now_playing[1],
				'title': now_playing[2],
				'total': now_playing[3],
			}

	def player_spotify(self, pl):
		try:
			import dbus
		except ImportError:
			sys.stderr.write('Could not add Spotify segment: Requires python-dbus.\n')
			return
		bus = dbus.SessionBus()
		DBUS_IFACE_PROPERTIES = 'org.freedesktop.DBus.Properties'
		DBUS_IFACE_PLAYER = 'org.freedesktop.MediaPlayer2'
		try:
			player = bus.get_object('com.spotify.qt', '/')
			iface = dbus.Interface(player, DBUS_IFACE_PROPERTIES)
			info = iface.Get(DBUS_IFACE_PLAYER, 'Metadata')
			status = iface.Get(DBUS_IFACE_PLAYER, 'PlaybackStatus')
		except dbus.exceptions.DBusException:
			return
		if not info:
			return
		state = self._convert_state(status)
		return {
			'state': state,
			'state_symbol': self.STATE_SYMBOLS.get(state),
			'album': info.get('xesam:album'),
			'artist': info.get('xesam:artist')[0],
			'title': info.get('xesam:title'),
			'total': self._convert_seconds(info.get('mpris:length') / 1e6),
		}

	def player_rhythmbox(self, pl):
		now_playing = self._run_cmd(['rhythmbox-client', '--no-start', '--no-present', '--print-playing-format', '%at\n%aa\n%tt\n%te\n%td'])
		if not now_playing:
			return
		now_playing = now_playing.split('\n')
		return {
			'album': now_playing[0],
			'artist': now_playing[1],
			'title': now_playing[2],
			'elapsed': now_playing[3],
			'total': now_playing[4],
		}
now_playing = NowPlayingSegment()


if os.path.exists('/sys/class/power_supply/BAT0/capacity'):
	def _get_capacity():
		with open('/sys/class/power_supply/BAT0/capacity', 'r') as f:
			return int(float(f.readline().split()[0]))
else:
	def _get_capacity():
		raise NotImplementedError


def battery(pl, format='{batt:3.0%}', steps=5, gamify=False):
	'''Return battery charge status.

	:param int steps:
		number of discrete steps to show between 0% and 100% capacity
	:param bool gamify:
		measure in hearts (♥) instead of percentages

	Highlight groups used: ``battery_gradient`` (gradient), ``battery``.
	'''
	try:
		capacity = _get_capacity()
	except NotImplementedError:
		pl.warn('Unable to get battery capacity.')
		return None
	ret = []
	denom = int(steps)
	numer = int(denom * capacity / 100)
	full_heart = '♥'
	if gamify:
		ret.append({
			'contents': full_heart * numer,
			'draw_soft_divider': False,
			'highlight_group': ['battery_gradient', 'battery'],
			'gradient_level': 99
		})
		ret.append({
			'contents': full_heart * (denom - numer),
			'draw_soft_divider': False,
			'highlight_group': ['battery_gradient', 'battery'],
			'gradient_level': 1
		})
	else:
		batt = numer / float(denom)
		ret.append({
			'contents': format.format(batt=batt),
			'highlight_group': ['battery_gradient', 'battery'],
			'gradient_level': batt * 100
		})
	return ret
