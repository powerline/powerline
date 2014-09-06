# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import sys
import re
import socket

from datetime import datetime
from multiprocessing import cpu_count as _cpu_count
from collections import namedtuple

from powerline.lib import add_divider_highlight_group
from powerline.lib.shell import asrun, run_cmd
from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.vcs import guess, tree_status
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment
from powerline.lib.monotonic import monotonic
from powerline.lib.humanize_bytes import humanize_bytes
from powerline.lib.unicode import u
from powerline.theme import requires_segment_info, requires_filesystem_watcher
from powerline.segments import Segment, with_docstring


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


@requires_filesystem_watcher
@requires_segment_info
def branch(pl, segment_info, create_watcher, status_colors=False):
	'''Return the current VCS branch.

	:param bool status_colors:
		determines whether repository status will be used to determine highlighting. Default: False.

	Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.
	'''
	name = segment_info['getcwd']()
	repo = guess(path=name, create_watcher=create_watcher)
	if repo is not None:
		branch = repo.branch()
		scol = ['branch']
		if status_colors:
			try:
				status = tree_status(repo, pl)
			except Exception as e:
				pl.exception('Failed to compute tree status: {0}', str(e))
				status = '?'
			scol.insert(0, 'branch_dirty' if status and status.strip() else 'branch_clean')
		return [{
			'contents': branch,
			'highlight_group': scol,
		}]


@requires_segment_info
class CwdSegment(Segment):
	def argspecobjs(self):
		for obj in super(CwdSegment, self).argspecobjs():
			yield obj
		yield 'get_shortened_path', self.get_shortened_path

	def omitted_args(self, name, method):
		if method is self.get_shortened_path:
			return (0, 1, 2)
		else:
			return super(CwdSegment, self).omitted_args(name, method)

	def get_shortened_path(self, pl, segment_info, shorten_home=True, **kwargs):
		try:
			path = u(segment_info['getcwd']())
		except OSError as e:
			if e.errno == 2:
				# user most probably deleted the directory
				# this happens when removing files from Mercurial repos for example
				pl.warn('Current directory not found')
				return "[not found]"
			else:
				raise
		if shorten_home:
			home = segment_info['home']
			if home:
				home = u(home)
				if path.startswith(home):
					path = '~' + path[len(home):]
		return path

	def __call__(self, pl, segment_info,
	             dir_shorten_len=None,
	             dir_limit_depth=None,
	             use_path_separator=False,
	             ellipsis='...',
	             **kwargs):
		cwd = self.get_shortened_path(pl, segment_info, **kwargs)
		cwd_split = cwd.split(os.sep)
		cwd_split_len = len(cwd_split)
		cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
		if dir_limit_depth and cwd_split_len > dir_limit_depth + 1:
			del(cwd[0:-dir_limit_depth])
			if ellipsis is not None:
				cwd.insert(0, ellipsis)
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


cwd = with_docstring(CwdSegment(),
'''Return the current working directory.

Returns a segment list to create a breadcrumb-like effect.

:param int dir_shorten_len:
	shorten parent directory names to this length (e.g. 
	:file:`/long/path/to/powerline` → :file:`/l/p/t/powerline`)
:param int dir_limit_depth:
	limit directory depth to this number (e.g. 
	:file:`/long/path/to/powerline` → :file:`⋯/to/powerline`)
:param bool use_path_separator:
	Use path separator in place of soft divider.
:param bool shorten_home:
	Shorten home directory to ``~``.
:param str ellipsis:
	Specifies what to use in place of omitted directories. Use None to not 
	show this subsegment at all.

Divider highlight group used: ``cwd:divider``.

Highlight groups used: ``cwd:current_folder`` or ``cwd``. It is recommended to define all highlight groups.
''')


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
		'highlight_group': (['time'] if istime else []) + ['date'],
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

:param str query_url:
	URI to query for IP address, should return only the IP address as a text string

	Suggested URIs:

	* http://ipv4.icanhazip.com/
	* http://ipv6.icanhazip.com/
	* http://icanhazip.com/ (returns IPv6 address if available, else IPv4)

Divider highlight group used: ``background:divider``.
''')


try:
	import netifaces
except ImportError:
	def internal_ip(pl, interface='detect', ipv=4):
		return None
else:
	_interface_starts = {
		'eth':   10,  # Regular ethernet adapters         : eth1
		'enp':   10,  # Regular ethernet adapters, Gentoo : enp2s0
		'ath':    9,  # Atheros WiFi adapters             : ath0
		'wlan':   9,  # Other WiFi adapters               : wlan1
		'wlp':    9,  # Other WiFi adapters, Gentoo       : wlp5s0
		'teredo': 1,  # miredo interface                  : teredo
		'lo':   -10,  # Loopback interface                : lo
	}

	_interface_start_re = re.compile(r'^([a-z]+?)(\d|$)')

	def _interface_key(interface):
		match = _interface_start_re.match(interface)
		if match:
			try:
				base = _interface_starts[match.group(1)] * 100
			except KeyError:
				base = 500
			if match.group(2):
				return base - int(match.group(2))
			else:
				return base
		else:
			return 0

	def internal_ip(pl, interface='detect', ipv=4):
		if interface == 'detect':
			try:
				interface = next(iter(sorted(netifaces.interfaces(), key=_interface_key, reverse=True)))
			except StopIteration:
				pl.info('No network interfaces found')
				return None
		addrs = netifaces.ifaddresses(interface)
		try:
			return addrs[netifaces.AF_INET6 if ipv == 6 else netifaces.AF_INET][0]['addr']
		except (KeyError, IndexError):
			return None


internal_ip = with_docstring(internal_ip,
'''Return internal IP address

Requires ``netifaces`` module to work properly.

:param str interface:
	Interface on which IP will be checked. Use ``detect`` to automatically 
	detect interface. In this case interfaces with lower numbers will be 
	preferred over interfaces with similar names. Order of preference based on 
	names:

	#. ``eth`` and ``enp`` followed by number or the end of string.
	#. ``ath``, ``wlan`` and ``wlp`` followed by number or the end of string.
	#. ``teredo`` followed by number or the end of string.
	#. Any other interface that is not ``lo*``.
	#. ``lo`` followed by number or the end of string.
:param int ipv:
	4 or 6 for ipv4 and ipv6 respectively, depending on which IP address you 
	need exactly.
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
	'day':           'DAY',
	'blustery':      'WIND',
	'rainy':         'RAIN',
	'cloudy':        'CLOUDS',
	'snowy':         'SNOW',
	'stormy':        'STORM',
	'foggy':         'FOG',
	'sunny':         'SUN',
	'night':         'NIGHT',
	'windy':         'WINDY',
	'not_available': 'NA',
	'unknown':       'UKN',
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
				self.location = ','.join((
					location_data['city'],
					location_data['region_code'],
					location_data['country_code']
				))
			query_data = {
				'q':
				'use "https://raw.githubusercontent.com/yql/yql-tables/master/weather/weather.bylocation.xml" as we;'
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

	# psutil-2.0.0: psutil.Process.username is unbound method
	if callable(psutil.Process.username):
		def _get_user(segment_info):
			return psutil.Process(os.getpid()).username()
	# pre psutil-2.0.0: psutil.Process.username has type property
	else:
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
	def _get_bytes(interface):
		with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
			rx = int(file_obj.read())
		with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
			tx = int(file_obj.read())
		return (rx, tx)

	def _get_interfaces():
		for interface in os.listdir('/sys/class/net'):
			x = _get_bytes(interface)
			if x is not None:
				yield interface, x[0], x[1]

	def _get_user(segment_info):
		return segment_info['environ'].get('USER', None)

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
		'highlight_group': ['user'] if euid != 0 else ['superuser', 'user'],
	}]
if 'psutil' not in globals():
	user = requires_segment_info(user)


if os.path.exists('/proc/uptime'):
	def _get_uptime():
		with open('/proc/uptime', 'r') as f:
			return int(float(f.readline().split()[0]))
elif 'psutil' in globals():
	from time import time

	def _get_uptime():
		# psutil.BOOT_TIME is not subject to clock adjustments, but time() is.
		# Thus it is a fallback to /proc/uptime reading and not the reverse.
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


class NetworkLoadSegment(KwThreadedSegment):
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

	def render_one(self, idata, recv_format='DL {value:>8}', sent_format='UL {value:>8}', suffix='B/s', si_prefix=False, **kwargs):
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
		except imaplib.IMAP4.error as e:
			unread_count = str(e)
		else:
			mail = imaplib.IMAP4_SSL(key.server, key.port)
			mail.login(key.username, key.password)
			rc, message = mail.status(key.folder, '(UNSEEN)')
			unread_str = message[0].decode('utf-8')
			unread_count = int(re.search('UNSEEN (\d+)', unread_str).group(1))
		return unread_count

	@staticmethod
	def render_one(unread_count, max_msgs=None, **kwargs):
		if not unread_count:
			return None
		elif type(unread_count) != int or not max_msgs:
			return [{
				'contents': str(unread_count),
				'highlight_group': ['email_alert'],
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


STATE_SYMBOLS = {
	'fallback': '',
	'play': '>',
	'pause': '~',
	'stop': 'X',
}


class NowPlayingSegment(Segment):
	def __call__(self, player='mpd', format='{state_symbol} {artist} - {title} ({total})', state_symbols=STATE_SYMBOLS, **kwargs):
		player_func = getattr(self, 'player_{0}'.format(player))
		stats = {
			'state': 'fallback',
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
		stats['state_symbol'] = state_symbols.get(stats['state'])
		return format.format(**stats)

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
		now_playing_str = run_cmd(pl, ['cmus-remote', '-Q'])
		if not now_playing_str:
			return
		ignore_levels = ('tag', 'set',)
		now_playing = dict(((token[0] if token[0] not in ignore_levels else token[1],
			(' '.join(token[1:]) if token[0] not in ignore_levels else
			' '.join(token[2:]))) for token in [line.split(' ') for line in now_playing_str.split('\n')[:-1]]))
		state = self._convert_state(now_playing.get('status'))
		return {
			'state': state,
			'album': now_playing.get('album'),
			'artist': now_playing.get('artist'),
			'title': now_playing.get('title'),
			'elapsed': self._convert_seconds(now_playing.get('position', 0)),
			'total': self._convert_seconds(now_playing.get('duration', 0)),
		}

	def player_mpd(self, pl, host='localhost', port=6600):
		try:
			import mpd
		except ImportError:
			now_playing = run_cmd(pl, ['mpc', 'current', '-f', '%album%\n%artist%\n%title%\n%time%', '-h', str(host), '-p', str(port)])
			if not now_playing:
				return
			now_playing = now_playing.split('\n')
			return {
				'album': now_playing[0],
				'artist': now_playing[1],
				'title': now_playing[2],
				'total': now_playing[3],
			}
		else:
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
				'album': now_playing.get('album'),
				'artist': now_playing.get('artist'),
				'title': now_playing.get('title'),
				'elapsed': self._convert_seconds(now_playing.get('elapsed', 0)),
				'total': self._convert_seconds(now_playing.get('time', 0)),
			}

	def player_dbus(self, player_name, bus_name, player_path, iface_prop, iface_player):
		try:
			import dbus
		except ImportError:
			pl.exception('Could not add {0} segment: requires dbus module', player_name)
			return
		bus = dbus.SessionBus()
		try:
			player = bus.get_object(bus_name, player_path)
			iface = dbus.Interface(player, iface_prop)
			info = iface.Get(iface_player, 'Metadata')
			status = iface.Get(iface_player, 'PlaybackStatus')
		except dbus.exceptions.DBusException:
			return
		if not info:
			return
		album = u(info.get('xesam:album'))
		title = u(info.get('xesam:title'))
		artist = info.get('xesam:artist')
		state = self._convert_state(status)
		if artist:
			artist = u(artist[0])
		return {
			'state': state,
			'album': album,
			'artist': artist,
			'title': title,
			'total': self._convert_seconds(info.get('mpris:length') / 1e6),
		}

	def player_spotify_dbus(self, pl):
		return self.player_dbus(
			player_name='Spotify',
			bus_name='com.spotify.qt',
			player_path='/',
			iface_prop='org.freedesktop.DBus.Properties',
			iface_player='org.freedesktop.MediaPlayer2',
		)

	def player_clementine(self, pl):
		return self.player_dbus(
			player_name='Clementine',
			bus_name='org.mpris.MediaPlayer2.clementine',
			player_path='/org/mpris/MediaPlayer2',
			iface_prop='org.freedesktop.DBus.Properties',
			iface_player='org.mpris.MediaPlayer2.Player',
		)

	def player_spotify_apple_script(self, pl):
		status_delimiter = '-~`/='
		ascript = '''
			tell application "System Events"
				set process_list to (name of every process)
			end tell

			if process_list contains "Spotify" then
				tell application "Spotify"
					if player state is playing or player state is paused then
						set track_name to name of current track
						set artist_name to artist of current track
						set album_name to album of current track
						set track_length to duration of current track
						set now_playing to "" & player state & "{0}" & album_name & "{0}" & artist_name & "{0}" & track_name & "{0}" & track_length
						return now_playing
					else
						return player state
					end if

				end tell
			else
				return "stopped"
			end if
		'''.format(status_delimiter)

		spotify = asrun(pl, ascript)
		if not asrun:
			return None

		spotify_status = spotify.split(status_delimiter)
		state = self._convert_state(spotify_status[0])
		if state == 'stop':
			return None
		return {
			'state': state,
			'album': spotify_status[1],
			'artist': spotify_status[2],
			'title': spotify_status[3],
			'total': self._convert_seconds(int(spotify_status[4]))
		}

	try:
		__import__('dbus')
	except ImportError:
		if sys.platform.startswith('darwin'):
			player_spotify = player_spotify_apple_script
		else:
			player_spotify = player_spotify_dbus
	else:
		player_spotify = player_spotify_dbus

	def player_rhythmbox(self, pl):
		now_playing = run_cmd(pl, ['rhythmbox-client', '--no-start', '--no-present', '--print-playing-format', '%at\n%aa\n%tt\n%te\n%td'])
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

	def player_rdio(self, pl):
		status_delimiter = '-~`/='
		ascript = '''
			tell application "System Events"
				set rdio_active to the count(every process whose name is "Rdio")
				if rdio_active is 0 then
					return
				end if
			end tell
			tell application "Rdio"
				set rdio_name to the name of the current track
				set rdio_artist to the artist of the current track
				set rdio_album to the album of the current track
				set rdio_duration to the duration of the current track
				set rdio_state to the player state
				set rdio_elapsed to the player position
				return rdio_name & "{0}" & rdio_artist & "{0}" & rdio_album & "{0}" & rdio_elapsed & "{0}" & rdio_duration & "{0}" & rdio_state
			end tell
		'''.format(status_delimiter)
		now_playing = asrun(pl, ascript)
		if not now_playing:
			return
		now_playing = now_playing.split('\n')
		if len(now_playing) != 6:
			return
		state = self._convert_state(now_playing[5])
		total = self._convert_seconds(now_playing[4])
		elapsed = self._convert_seconds(float(now_playing[3]) * float(now_playing[4]) / 100)
		return {
			'title': now_playing[0],
			'artist': now_playing[1],
			'album': now_playing[2],
			'elapsed': elapsed,
			'total': total,
			'state': state,
			'state_symbol': self.STATE_SYMBOLS.get(state)
		}
now_playing = NowPlayingSegment()


def _get_battery(pl):
	try:
		import dbus
	except ImportError:
		pl.debug('Not using DBUS+UPower as dbus is not available')
	else:
		try:
			bus = dbus.SystemBus()
		except Exception as e:
			pl.exception('Failed to connect to system bus: {0}', str(e))
		else:
			interface = 'org.freedesktop.UPower'
			try:
				up = bus.get_object(interface, '/org/freedesktop/UPower')
			except dbus.exceptions.DBusException as e:
				if getattr(e, '_dbus_error_name', '').endswidth('ServiceUnknown'):
					pl.debug('Not using DBUS+UPower as UPower is not available via dbus')
				else:
					pl.exception('Failed to get UPower service with dbus: {0}', str(e))
			else:
				devinterface = 'org.freedesktop.DBus.Properties'
				devtype_name = interface + '.Device'
				for devpath in up.EnumerateDevices(dbus_interface=interface):
					dev = bus.get_object(interface, devpath)
					devget = lambda what: dev.Get(
						devtype_name,
						what,
						dbus_interface=devinterface
					)
					if int(devget('Type')) != 2:
						pl.debug('Not using DBUS+UPower with {0}: invalid type', devpath)
						continue
					if not bool(devget('IsPresent')):
						pl.debug('Not using DBUS+UPower with {0}: not present', devpath)
						continue
					if not bool(devget('PowerSupply')):
						pl.debug('Not using DBUS+UPower with {0}: not a power supply', devpath)
						continue
					pl.debug('Using DBUS+UPower with {0}', devpath)
					return lambda pl: float(
						dbus.Interface(dev, dbus_interface=devinterface).Get(
							devtype_name,
							'Percentage'
						)
					)
				pl.debug('Not using DBUS+UPower as no batteries were found')

	if os.path.isdir('/sys/class/power_supply'):
		linux_bat_fmt = '/sys/class/power_supply/{0}/capacity'
		for linux_bat in os.listdir('/sys/class/power_supply'):
			cap_path = linux_bat_fmt.format(linux_bat)
			if linux_bat.startswith('BAT') and os.path.exists(cap_path):
				pl.debug('Using /sys/class/power_supply with battery {0}', linux_bat)

				def _get_capacity(pl):
					with open(cap_path, 'r') as f:
						return int(float(f.readline().split()[0]))

				return _get_capacity
		pl.debug('Not using /sys/class/power_supply as no batteries were found')
	else:
		pl.debug('Not using /sys/class/power_supply: no directory')

	try:
		from shutil import which  # Python-3.3 and later
	except ImportError:
		pl.info('Using dumb “which” which only checks for file in /usr/bin')
		which = lambda f: (lambda fp: os.path.exists(fp) and fp)(os.path.join('/usr/bin', f))

	if which('pmset'):
		pl.debug('Using pmset')

		def _get_capacity(pl):
			import re
			battery_summary = run_cmd(pl, ['pmset', '-g', 'batt'])
			battery_percent = re.search(r'(\d+)%', battery_summary).group(1)
			return int(battery_percent)

		return _get_capacity
	else:
		pl.debug('Not using pmset: executable not found')

	if sys.platform.startswith('win'):
		# From http://stackoverflow.com/a/21083571/273566, reworked
		try:
			from win32com.client import GetObject
		except ImportError:
			pl.debug('Not using win32com.client as it is not available')
		else:
			try:
				wmi = GetObject('winmgmts:')
			except Exception as e:
				pl.exception('Failed to run GetObject from win32com.client: {0}', str(e))
			else:
				for battery in wmi.InstancesOf('Win32_Battery'):
					pl.debug('Using win32com.client with Win32_Battery')

					def _get_capacity(pl):
						# http://msdn.microsoft.com/en-us/library/aa394074(v=vs.85).aspx
						return battery.EstimatedChargeRemaining

					return _get_capacity
				pl.debug('Not using win32com.client as no batteries were found')

		from ctypes import Structure, c_byte, c_ulong, windll, byref

		class PowerClass(Structure):
			_fields_ = [
				('ACLineStatus', c_byte),
				('BatteryFlag', c_byte),
				('BatteryLifePercent', c_byte),
				('Reserved1', c_byte),
				('BatteryLifeTime', c_ulong),
				('BatteryFullLifeTime', c_ulong)
			]

		def _get_capacity(pl):
			powerclass = PowerClass()
			result = windll.kernel32.GetSystemPowerStatus(byref(powerclass))
			# http://msdn.microsoft.com/en-us/library/windows/desktop/aa372693(v=vs.85).aspx
			if result:
				return None
			return powerclass.BatteryLifePercent

		if _get_capacity() is None:
			pl.debug('Not using GetSystemPowerStatus because it failed')
		else:
			pl.debug('Using GetSystemPowerStatus')

		return _get_capacity

	raise NotImplementedError


def _get_capacity(pl):
	global _get_capacity

	def _failing_get_capacity(pl):
		raise NotImplementedError

	try:
		_get_capacity = _get_battery(pl)
	except NotImplementedError:
		_get_capacity = _failing_get_capacity
	except Exception as e:
		pl.exception('Exception while obtaining battery capacity getter: {0}', str(e))
		_get_capacity = _failing_get_capacity
	return _get_capacity(pl)


def battery(pl, format='{capacity:3.0%}', steps=5, gamify=False, full_heart='O', empty_heart='O'):
	'''Return battery charge status.

	:param str format:
		Percent format in case gamify is False.
	:param int steps:
		Number of discrete steps to show between 0% and 100% capacity if gamify
		is True.
	:param bool gamify:
		Measure in hearts (♥) instead of percentages. For full hearts 
		``battery_full`` highlighting group is preferred, for empty hearts there 
		is ``battery_empty``.
	:param str full_heart:
		Heart displayed for “full” part of battery.
	:param str empty_heart:
		Heart displayed for “used” part of battery. It is also displayed using
		another gradient level and highlighting group, so it is OK for it to be 
		the same as full_heart as long as necessary highlighting groups are 
		defined.

	``battery_gradient`` and ``battery`` groups are used in any case, first is 
	preferred.

	Highlight groups used: ``battery_full`` or ``battery_gradient`` (gradient) or ``battery``, ``battery_empty`` or ``battery_gradient`` (gradient) or ``battery``.
	'''
	try:
		capacity = _get_capacity(pl)
	except NotImplementedError:
		pl.info('Unable to get battery capacity.')
		return None
	ret = []
	if gamify:
		denom = int(steps)
		numer = int(denom * capacity / 100)
		ret.append({
			'contents': full_heart * numer,
			'draw_inner_divider': False,
			'highlight_group': ['battery_full', 'battery_gradient', 'battery'],
			# Using zero as “nothing to worry about”: it is least alert color.
			'gradient_level': 0,
		})
		ret.append({
			'contents': empty_heart * (denom - numer),
			'draw_inner_divider': False,
			'highlight_group': ['battery_empty', 'battery_gradient', 'battery'],
			# Using a hundred as it is most alert color.
			'gradient_level': 100,
		})
	else:
		ret.append({
			'contents': format.format(capacity=(capacity / 100.0)),
			'highlight_group': ['battery_gradient', 'battery'],
			# Gradients are “least alert – most alert” by default, capacity has 
			# the opposite semantics.
			'gradient_level': 100 - capacity,
		})
	return ret
