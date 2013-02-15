# -*- coding: utf-8 -*-

import os
import sys

from powerline.lib import memoize, urllib_read, urllib_urlencode


def hostname(only_if_ssh=False):
	'''Return the current hostname.

	:param bool only_if_ssh:
		only return the hostname if currently in an SSH session
	'''
	import socket
	if only_if_ssh and not os.environ.get('SSH_CLIENT'):
		return None
	return socket.gethostname()


def user():
	'''Return the current user.

	Highlights the user with the ``superuser`` if the effective user ID is 0.
	'''
	user = os.environ.get('USER')
	euid = os.geteuid()
	return [{
			'contents': user,
			'highlight_group': 'user' if euid != 0 else ['superuser', 'user'],
		}]


def branch():
	'''Return the current VCS branch.'''
	from powerline.lib.vcs import guess
	repo = guess(path=os.path.abspath(os.getcwd()))
	if repo:
		return repo.branch()
	return None


def cwd(dir_shorten_len=None, dir_limit_depth=None):
	'''Return the current working directory.

	Returns a segment list to create a breadcrumb-like effect.

	:param int dir_shorten_len:
		shorten parent directory names to this length (e.g. :file:`/long/path/to/powerline` → :file:`/l/p/t/powerline`)
	:param int dir_limit_depth:
		limit directory depth to this number (e.g. :file:`/long/path/to/powerline` → :file:`⋯/to/powerline`)
	'''
	import re
	try:
		cwd = os.getcwdu()
	except AttributeError:
		cwd = os.getcwd()
	home = os.environ.get('HOME')
	if home:
		cwd = re.sub('^' + re.escape(home), '~', cwd, 1)
	cwd_split = cwd.split(os.sep)
	cwd_split_len = len(cwd_split)
	if cwd_split_len > dir_limit_depth + 1:
		del(cwd_split[0:-dir_limit_depth])
		cwd_split.insert(0, u'⋯')
	cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
	ret = []
	if not cwd[0]:
		cwd[0] = '/'
	for part in cwd:
		if not part:
			continue
		ret.append({
			'contents': part,
			})
	ret[-1]['highlight_group'] = ['cwd:current_folder', 'cwd']
	return ret


def date(format='%Y-%m-%d'):
	'''Return the current date.

	:param str format:
		strftime-style date format string
	'''
	from datetime import datetime
	return datetime.now().strftime(format)


def fuzzy_time():
	'''Display the current time as fuzzy time, e.g. "quarter past six".'''
	from datetime import datetime

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


@memoize(600)
def external_ip(query_url='http://ipv4.icanhazip.com/'):
	'''Return external IP address.

	Suggested URIs:

	* http://ipv4.icanhazip.com/
	* http://ipv6.icanhazip.com/
	* http://icanhazip.com/ (returns IPv6 address if available, else IPv4)

	:param str query_url:
		URI to query for IP address, should return only the IP address as a text string
	'''
	return urllib_read(query_url).strip()


def uptime(format='{days:02d}d {hours:02d}h {minutes:02d}m'):
	'''Return system uptime.

	Uses the ``psutil`` module if available for multi-platform compatibility,
	falls back to reading :file:`/proc/uptime`.

	:param str format:
		format string, will be passed ``days``, ``hours`` and ``minutes`` as arguments
	'''
	try:
		import psutil
		from datetime import datetime
		seconds = int((datetime.now() - datetime.fromtimestamp(psutil.BOOT_TIME)).total_seconds())
	except ImportError:
		try:
			with open('/proc/uptime', 'r') as f:
				seconds = int(float(f.readline().split()[0]))
		except IOError:
			return None
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	return format.format(days=int(days), hours=hours, minutes=minutes)


# Weather condition code descriptions available at
# http://developer.yahoo.com/weather/#codes
weather_conditions_codes = (
	('tornado',                 'stormy'), #  0
	('tropical_storm',          'stormy'), #  1
	('hurricane',               'stormy'), #  2
	('severe_thunderstorms',    'stormy'), #  3
	('thunderstorms',           'stormy'), #  4
	('mixed_rain_and_snow',     'rainy' ), #  5
	('mixed_rain_and_sleet',    'rainy' ), #  6
	('mixed_snow_and_sleet',    'snowy' ), #  7
	('freezing_drizzle',        'rainy' ), #  8
	('drizzle',                 'rainy' ), #  9
	('freezing_rain',           'rainy' ), # 10
	('showers',                 'rainy' ), # 11
	('showers',                 'rainy' ), # 12
	('snow_flurries',           'snowy' ), # 13
	('light_snow_showers',      'snowy' ), # 14
	('blowing_snow',            'snowy' ), # 15
	('snow',                    'snowy' ), # 16
	('hail',                    'snowy' ), # 17
	('sleet',                   'snowy' ), # 18
	('dust',                    'foggy' ), # 19
	('fog',                     'foggy' ), # 20
	('haze',                    'foggy' ), # 21
	('smoky',                   'foggy' ), # 22
	('blustery',                'foggy' ), # 23
	('windy',                           ), # 24
	('cold',                    'day'   ), # 25
	('clouds',                  'cloudy'), # 26
	('mostly_cloudy_night',     'cloudy'), # 27
	('mostly_cloudy_day',       'cloudy'), # 28
	('partly_cloudy_night',     'cloudy'), # 29
	('partly_cloudy_day',       'cloudy'), # 30
	('clear_night',             'night' ), # 31
	('sun',                     'sunny' ), # 32
	('fair_night',              'night' ), # 33
	('fair_day',                'day'   ), # 34
	('mixed_rain_and_hail',     'rainy' ), # 35
	('hot',                     'sunny' ), # 36
	('isolated_thunderstorms',  'stormy'), # 37
	('scattered_thunderstorms', 'stormy'), # 38
	('scattered_thunderstorms', 'stormy'), # 39
	('scattered_showers',       'rainy' ), # 40
	('heavy_snow',              'snowy' ), # 41
	('scattered_snow_showers',  'snowy' ), # 42
	('heavy_snow',              'snowy' ), # 43
	('partly_cloudy',           'cloudy'), # 44
	('thundershowers',          'rainy' ), # 45
	('snow_showers',            'snowy' ), # 46
	('isolated_thundershowers', 'rainy' ), # 47
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
	'day':           u'〇',
	'blustery':      u'⚑',
	'rainy':         u'☔',
	'cloudy':        u'☁',
	'snowy':         u'❅',
	'stormy':        u'☈',
	'foggy':         u'〰',
	'sunny':         u'☼',
	'night':         u'☾',
	'windy':         u'☴',
	'not_available': u'�',
	'unknown':       u'⚠',
}


@memoize(1800)
def weather(unit='c', location_query=None, icons=None):
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
	'''
	import json

	if not location_query:
		try:
			location = json.loads(urllib_read('http://freegeoip.net/json/' + external_ip()))
			location_query = ','.join([location['city'], location['region_name'], location['country_name']])
		except (TypeError, ValueError):
			return None
	query_data = {
		'q':
			u'use "http://github.com/yql/yql-tables/raw/master/weather/weather.bylocation.xml" as we;'
			u'select * from we where location="{0}" and unit="{1}"'.format(location_query, unit).encode('utf-8'),
		'format': 'json'
	}
	try:
		url = 'http://query.yahooapis.com/v1/public/yql?' + urllib_urlencode(query_data)
		response = json.loads(urllib_read(url))
		condition = response['query']['results']['weather']['rss']['channel']['item']['condition']
		condition_code = int(condition['code'])
	except (KeyError, TypeError, ValueError):
		return None

	try:
		icon_names = weather_conditions_codes[condition_code]
	except IndexError:
		icon_names = (('not_available' if condition_code == 3200 else 'unknown'),)

	for icon_name in icon_names:
		if icons:
			if icon_name in icons:
				icon = icons[icon_name]
				break
	else:
		icon = weather_conditions_icons[icon_names[-1]]

	groups = ['weather_condition_' + icon_name for icon_name in icon_names] + ['weather_conditions', 'weather']
	return [
			{
			'contents': icon + ' ',
			'highlight_group': groups,
			},
			{
			'contents': u'{0}°{1}'.format(condition['temp'], unit.upper()),
			'highlight_group': ['weather_temp_cold' if int(condition['temp']) < 0 else 'weather_temp_hot', 'weather_temp', 'weather'],
			'draw_divider': False,
			},
		]


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
	'''
	import multiprocessing
	cpu_count = multiprocessing.cpu_count()
	ret = []
	for avg in os.getloadavg():
		normalized = avg / cpu_count
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
			})
	ret[0]['draw_divider'] = True
	ret[0]['contents'] += ' '
	ret[1]['contents'] += ' '
	return ret


def cpu_load_percent(measure_interval=.5):
	'''Return the average CPU load as a percentage.

	Requires the ``psutil`` module.

	:param float measure_interval:
		interval used to measure CPU load (in seconds)
	'''
	try:
		import psutil
	except ImportError:
		return None
	cpu_percent = int(psutil.cpu_percent(interval=measure_interval))
	return u'{0}%'.format(cpu_percent)


def network_load(interface='eth0', measure_interval=1, suffix='B/s', binary_prefix=False):
	'''Return the network load.

	Uses the ``psutil`` module if available for multi-platform compatibility,
	falls back to reading
	:file:`/sys/class/net/{interface}/statistics/{rx,tx}_bytes`.

	:param str interface:
		network interface to measure
	:param float measure_interval:
		interval used to measure the network load (in seconds)
	:param str suffix:
		string appended to each load string
	:param bool binary_prefix:
		use binary prefix, e.g. MiB instead of MB
	'''
	import time
	from powerline.lib import humanize_bytes

	def get_bytes():
		try:
			import psutil
			io_counters = psutil.network_io_counters(pernic=True)
			if_io = io_counters.get(interface)
			if not if_io:
				return None
			return (if_io.bytes_recv, if_io.bytes_sent)
		except ImportError:
			try:
				with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
					rx = int(file_obj.read())
				with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
					tx = int(file_obj.read())
				return (rx, tx)
			except IOError:
				return None

	b1 = get_bytes()
	if b1 is None:
		return None
	time.sleep(measure_interval)
	b2 = get_bytes()
	return u'⬇ {rx_diff} ⬆ {tx_diff}'.format(
		rx_diff=humanize_bytes((b2[0] - b1[0]) / measure_interval, suffix, binary_prefix).rjust(8),
		tx_diff=humanize_bytes((b2[1] - b1[1]) / measure_interval, suffix, binary_prefix).rjust(8),
		)


def virtualenv():
	'''Return the name of the current Python virtualenv.'''
	return os.path.basename(os.environ.get('VIRTUAL_ENV', '')) or None


@memoize(60)
def email_imap_alert(username, password, server='imap.gmail.com', port=993, folder='INBOX'):
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
	'''
	import imaplib
	import re

	if not username or not password:
		return None
	try:
		mail = imaplib.IMAP4_SSL(server, port)
		mail.login(username, password)
		rc, message = mail.status(folder, '(UNSEEN)')
		unread_str = message[0].decode('utf-8')
		unread_count = int(re.search('UNSEEN (\d+)', unread_str).group(1))
	except imaplib.IMAP4.error as e:
		unread_count = str(e)
	if not unread_count:
		return None
	return [{
		'highlight_group': 'email_alert',
		'contents': unread_count,
		}]


class NowPlayingSegment(object):
	STATE_SYMBOLS = {
		'fallback': u'♫',
		'play': u'▶',
		'pause': u'▮▮',
		'stop': u'■',
		}

	def __call__(self, player='mpd', format=u'{state_symbol} {artist} - {title} ({total})', *args, **kwargs):
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
		return u'{0:.0f}:{1:02.0f}'.format(*divmod(float(seconds), 60))

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
		now_playing = {token[0] if token[0] not in ignore_levels else token[1]:
			' '.join(token[1:]) if token[0] not in ignore_levels else
			' '.join(token[2:]) for token in [line.split(' ') for line in now_playing_str.split('\n')[:-1]]}
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
