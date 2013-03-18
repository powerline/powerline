# vim:fileencoding=utf-8:noet

from __future__ import absolute_import

import os
import sys

from datetime import datetime
import socket
from multiprocessing import cpu_count

from powerline.lib import add_divider_highlight_group
from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.vcs import guess
from powerline.lib.threaded import ThreadedSegment, KwThreadedSegment, with_docstring
from powerline.lib.time import monotonic
from powerline.lib.humanize_bytes import humanize_bytes
from collections import namedtuple


def hostname(only_if_ssh=False):
	'''Return the current hostname.

	:param bool only_if_ssh:
		only return the hostname if currently in an SSH session
	'''
	if only_if_ssh and not os.environ.get('SSH_CLIENT'):
		return None
	return socket.gethostname()


def branch(status_colors=True):
	'''Return the current VCS branch.

	:param bool status_colors:
		determines whether repository status will be used to determine highlighting. Default: True.

	Highlight groups used: ``branch_clean``, ``branch_dirty``, ``branch``.
	'''
	repo = guess(path=os.path.abspath(os.getcwd()))
	if repo:
		branch = repo.branch()
		if status_colors:
			return [{
				'contents': branch,
				'highlight_group': ['branch_dirty' if repo.status() else 'branch_clean', 'branch'],
				}]
		else:
			return branch
	return None


def cwd(dir_shorten_len=None, dir_limit_depth=None):
	'''Return the current working directory.

	Returns a segment list to create a breadcrumb-like effect.

	:param int dir_shorten_len:
		shorten parent directory names to this length (e.g. :file:`/long/path/to/powerline` → :file:`/l/p/t/powerline`)
	:param int dir_limit_depth:
		limit directory depth to this number (e.g. :file:`/long/path/to/powerline` → :file:`⋯/to/powerline`)


	Divider highlight group used: ``cwd:divider``.

	Highlight groups used: ``cwd:current_folder`` or ``cwd``. It is recommended to define all highlight groups.
	'''
	import re
	try:
		try:
			cwd = os.getcwdu()
		except AttributeError:
			cwd = os.getcwd()
	except OSError as e:
		if e.errno == 2:
			# user most probably deleted the directory
			# this happens when removing files from Mercurial repos for example
			cwd = "[not found]"
		else:
			raise
	home = os.environ.get('HOME')
	if home:
		cwd = re.sub('^' + re.escape(home), '~', cwd, 1)
	cwd_split = cwd.split(os.sep)
	cwd_split_len = len(cwd_split)
	if dir_limit_depth and cwd_split_len > dir_limit_depth + 1:
		del(cwd_split[0:-dir_limit_depth])
		cwd_split.insert(0, '⋯')
	cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
	ret = []
	if not cwd[0]:
		cwd[0] = '/'
	for part in cwd:
		if not part:
			continue
		ret.append({
			'contents': part,
			'divider_highlight_group': 'cwd:divider',
			})
	ret[-1]['highlight_group'] = ['cwd:current_folder', 'cwd']
	return ret


def date(format='%Y-%m-%d', istime=False):
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


def fuzzy_time():
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
	def set_state(self, query_url='http://ipv4.icanhazip.com/', **kwargs):
		super(ExternalIpSegment, self).set_state(**kwargs)
		self.query_url = query_url

	def update(self):
		ip = _external_ip(query_url=self.query_url)
		with self.write_lock:
			self.ip = ip

	def render(self):
		return [{'contents': self.ip, 'divider_highlight_group': 'background:divider'}]


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
		super(WeatherSegment, self).set_state(**kwargs)
		self.location = location_query
		self.url = None
		self.condition = {}

	def update(self):
		import json

		if not self.url:
			# Do not lock attribute assignments in this branch: they are used 
			# only in .update()
			if not self.location:
				try:
					location_data = json.loads(urllib_read('http://freegeoip.net/json/' + _external_ip()))
					self.location = ','.join([location_data['city'],
												location_data['region_name'],
												location_data['country_name']])
				except (TypeError, ValueError):
					return
			query_data = {
					'q':
						'use "http://github.com/yql/yql-tables/raw/master/weather/weather.bylocation.xml" as we;'
						'select * from we where location="{0}" and unit="c"'.format(self.location).encode('utf-8'),
					'format': 'json',
					}
			self.url = 'http://query.yahooapis.com/v1/public/yql?' + urllib_urlencode(query_data)

		try:
			raw_response = urllib_read(self.url)
			response = json.loads(raw_response)
			condition = response['query']['results']['weather']['rss']['channel']['item']['condition']
			condition_code = int(condition['code'])
			temp = float(condition['temp'])
		except (KeyError, TypeError, ValueError):
			return

		try:
			icon_names = weather_conditions_codes[condition_code]
		except IndexError:
			icon_names = (('not_available' if condition_code == 3200 else 'unknown'),)

		with self.write_lock:
			self.temp = temp
			self.icon_names = icon_names

	def render(self, icons=None, unit='C', temperature_format=None, **kwargs):
		if not hasattr(self, 'icon_names'):
			return None

		for icon_name in self.icon_names:
			if icons:
				if icon_name in icons:
					icon = icons[icon_name]
					break
		else:
			icon = weather_conditions_icons[self.icon_names[-1]]

		temperature_format = temperature_format or ('{temp:.0f}' + temp_units[unit])
		temp = temp_conversions[unit](self.temp)
		groups = ['weather_condition_' + icon_name for icon_name in self.icon_names] + ['weather_conditions', 'weather']
		return [
				{
				'contents': icon + ' ',
				'highlight_group': groups,
				'divider_highlight_group': 'background:divider',
				},
				{
				'contents': temperature_format.format(temp=temp),
				'highlight_group': ['weather_temp_cold' if int(self.temp) < 0 else 'weather_temp_hot', 'weather_temp', 'weather'],
				'draw_divider': False,
				'divider_highlight_group': 'background:divider',
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
:param str temperature_format:
	format string, receives ``temp`` as an argument. Should also hold unit.

Divider highlight group used: ``background:divider``.

Highlight groups used: ``weather_conditions`` or ``weather``, ``weather_temp_cold`` or ``weather_temp_hot`` or ``weather_temp`` or ``weather``.
Also uses ``weather_conditions_{condition}`` for all weather conditions supported by Yahoo.
''')


def system_load(format='{avg:.1f}', threshold_good=1, threshold_bad=2):
	'''Return normalized system load average.

	Highlights using ``system_load_good``, ``system_load_bad`` and
	``system_load_ugly`` highlighting groups, depending on the thresholds
	passed to the function.

	:param str format:
		format string, receives ``avg`` as an argument
	:param float threshold_good:
		threshold for "good load" highlighting
	:param float threshold_bad:
		threshold for "bad load" highlighting

	Divider highlight group used: ``background:divider``.

	Highlight groups used: ``system_load_good`` or ``system_load``, ``system_load_bad`` or ``system_load``, ``system_load_ugly`` or ``system_load``. It is recommended to define all highlight groups.
	'''
	global cpu_count
	try:
		cpu_num = cpu_count()
	except NotImplementedError:
		return None
	ret = []
	for avg in os.getloadavg():
		normalized = avg / cpu_num
		if normalized < threshold_good:
			hl = 'system_load_good'
		elif normalized < threshold_bad:
			hl = 'system_load_bad'
		else:
			hl = 'system_load_ugly'
		ret.append({
			'contents': format.format(avg=avg),
			'highlight_group': [hl, 'system_load'],
			'draw_divider': False,
			'divider_highlight_group': 'background:divider',
			})
	ret[0]['draw_divider'] = True
	ret[0]['contents'] += ' '
	ret[1]['contents'] += ' '
	return ret


try:
	import psutil

	def _get_bytes(interface):
		io_counters = psutil.network_io_counters(pernic=True)
		if_io = io_counters.get(interface)
		if not if_io:
			return None
		return if_io.bytes_recv, if_io.bytes_sent

	def _get_user():
		return psutil.Process(os.getpid()).username

	def cpu_load_percent(measure_interval=.5):
		'''Return the average CPU load as a percentage.

		Requires the ``psutil`` module.

		:param float measure_interval:
			interval used to measure CPU load (in seconds)
		'''
		cpu_percent = int(psutil.cpu_percent(interval=measure_interval))
		return '{0}%'.format(cpu_percent)
except ImportError:
	def _get_bytes(interface):  # NOQA
		try:
			with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
				rx = int(file_obj.read())
			with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
				tx = int(file_obj.read())
			return (rx, tx)
		except IOError:
			return None

	def _get_user():  # NOQA
		return os.environ.get('USER', None)

	def cpu_load_percent(measure_interval=.5):  # NOQA
		'''Return the average CPU load as a percentage.

		Requires the ``psutil`` module.

		:param float measure_interval:
			interval used to measure CPU load (in seconds)
		'''
		return None


username = False


def user():
	'''Return the current user.

	Highlights the user with the ``superuser`` if the effective user ID is 0.

	Highlight groups used: ``superuser`` or ``user``. It is recommended to define all highlight groups.
	'''
	global username
	if username is False:
		username = _get_user()
	if username is None:
		return None
	try:
		euid = os.geteuid()
	except AttributeError:
		# os.geteuid is not available on windows
		euid = 1
	return [{
			'contents': username,
			'highlight_group': 'user' if euid != 0 else ['superuser', 'user'],
		}]


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
def uptime(format='{days}d {hours:02d}h {minutes:02d}m'):
	'''Return system uptime.

	:param str format:
		format string, will be passed ``days``, ``hours``, ``minutes`` and 
		seconds as arguments

	Divider highlight group used: ``background:divider``.
	'''
	try:
		seconds = _get_uptime()
	except (IOError, NotImplementedError):
		return None
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	return format.format(days=int(days), hours=hours, minutes=minutes, seconds=seconds)


class NetworkLoadSegment(KwThreadedSegment):
	interfaces = {}

	@staticmethod
	def key(interface='eth0', **kwargs):
		return interface

	def compute_state(self, interface):
		if interface in self.interfaces:
			idata = self.interfaces[interface]
			try:
				idata['prev'] = idata['last']
			except KeyError:
				pass
		else:
			idata = {}
			if self.run_once:
				idata['prev'] = (monotonic(), _get_bytes(interface))
				self.sleep(0)
			self.interfaces[interface] = idata

		idata['last'] = (monotonic(), _get_bytes(interface))
		return idata

	def render_one(self, idata, format='⬇ {recv:>8} ⬆ {sent:>8}', suffix='B/s', si_prefix=False, **kwargs):
		if not idata or 'prev' not in idata:
			return None

		t1, b1 = idata['prev']
		t2, b2 = idata['last']
		measure_interval = t2 - t1

		if None in (b1, b2):
			return None

		return [{
				'contents': format.format(
					recv=humanize_bytes((b2[0] - b1[0]) / measure_interval, suffix, si_prefix),
					sent=humanize_bytes((b2[1] - b1[1]) / measure_interval, suffix, si_prefix),
					),
				'divider_highlight_group': 'background:divider',
				}]


network_load = with_docstring(NetworkLoadSegment(),
'''Return the network load.

Uses the ``psutil`` module if available for multi-platform compatibility,
falls back to reading
:file:`/sys/class/net/{interface}/statistics/{rx,tx}_bytes`.

:param str interface:
	network interface to measure
:param str suffix:
	string appended to each load string
:param bool si_prefix:
	use SI prefix, e.g. MB instead of MiB
:param str format:
	format string, receives ``recv`` and ``sent`` as arguments
''')


def virtualenv():
	'''Return the name of the current Python virtualenv.'''
	return os.path.basename(os.environ.get('VIRTUAL_ENV', '')) or None


_IMAPKey = namedtuple('Key', 'username password server port folder')


class EmailIMAPSegment(KwThreadedSegment):
	interval = 60

	@staticmethod
	def key(username, password, server='imap.gmail.com', port=993, folder='INBOX'):
		return _IMAPKey(username, password, server, port, folder)

	@staticmethod
	def compute_state(key):
		if not key.username or not key.password:
			return None
		try:
			import imaplib
			import re
			mail = imaplib.IMAP4_SSL(key.server, key.port)
			mail.login(key.username, key.password)
			rc, message = mail.status(key.folder, '(UNSEEN)')
			unread_str = message[0].decode('utf-8')
			unread_count = int(re.search('UNSEEN (\d+)', unread_str).group(1))
		except socket.gaierror:
			return None
		except imaplib.IMAP4.error as e:
			unread_count = str(e)
		if not unread_count:
			return None
		return [{
			'highlight_group': 'email_alert',
			'contents': str(unread_count),
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

Highlight groups used: ``email_alert``.
''')


class NowPlayingSegment(object):
	STATE_SYMBOLS = {
		'fallback': '♫',
		'play': '▶',
		'pause': '▮▮',
		'stop': '■',
		}

	def __call__(self, player='mpd', format='{state_symbol} {artist} - {title} ({total})', *args, **kwargs):
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
		func_stats = player_func(*args, **kwargs)
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

	def player_cmus(self):
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

	def player_mpd(self, host='localhost', port=6600):
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

	def player_spotify(self):
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

	def player_rhythmbox(self):
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
