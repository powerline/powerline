# -*- coding: utf-8 -*-

import os
import sys

from powerline.lib import memoize

# Weather condition code descriptions available at http://developer.yahoo.com/weather/#codes
weather_conditions_codes = {
	u'〇': [25, 34],
	u'⚑': [24],
	u'☔': [5, 6, 8, 9, 10, 11, 12, 35, 40, 45, 47],
	u'☁': [26, 27, 28, 29, 30, 44],
	u'❅': [7, 13, 14, 15, 16, 17, 18, 41, 42, 43, 46],
	u'☈': [0, 1, 2, 3, 4, 37, 38, 39],
	u'〰': [19, 20, 21, 22, 23],
	u'☼': [32, 36],
	u'☾': [31, 33],
}


def _urllib_read(url):
	try:
		import urllib.error
		import urllib.request
		try:
			return urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
		except:
			return
	except ImportError:
		import urllib2
		try:
			return urllib2.urlopen(url, timeout=5).read()
		except urllib2.HTTPError:
			return


def _urllib_urlencode(string):
	try:
		import urllib.parse
		return urllib.parse.urlencode(string)
	except ImportError:
		import urllib
		return urllib.urlencode(string)


def hostname(only_if_ssh=False):
	import socket
	if only_if_ssh and not os.environ.get('SSH_CLIENT'):
		return None
	return socket.gethostname()


def user():
	user = os.environ.get('USER')
	euid = os.geteuid()
	return [{
			'contents': user,
			'highlight_group': 'user' if euid != 0 else ['superuser', 'user'],
		}]


def branch():
	from powerline.lib.vcs import guess
	repo = guess(os.path.abspath(os.getcwd()))
	if repo:
		return repo.branch()
	return None


def cwd(dir_shorten_len=None, dir_limit_depth=None):
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
	from datetime import datetime
	return datetime.now().strftime(format)


@memoize(600)
def external_ip(query_url='http://ipv4.icanhazip.com/'):
	return _urllib_read(query_url).strip()


def uptime(format='{days:02d}d {hours:02d}h {minutes:02d}m'):
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


@memoize(1800)
def weather(unit='c', location_query=None):
	import json

	if not location_query:
		try:
			location = json.loads(_urllib_read('http://freegeoip.net/json/' + external_ip()))
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
		url = 'http://query.yahooapis.com/v1/public/yql?' + _urllib_urlencode(query_data)
		response = json.loads(_urllib_read(url))
		condition = response['query']['results']['weather']['rss']['channel']['item']['condition']
		condition_code = int(condition['code'])
	except (KeyError, ValueError):
		return None
	icon = u'〇'
	for icon, codes in weather_conditions_codes.items():
		if condition_code in codes:
			break
	return [
			{
			'contents': icon + ' ',
			'highlight_group': ['weather_condition_' + icon, 'weather_condition', 'weather'],
			},
			{
			'contents': u'{0}°{1}'.format(condition['temp'], unit.upper()),
			'highlight_group': ['weather_temp_cold' if int(condition['temp']) < 0 else 'weather_temp_hot', 'weather_temp', 'weather'],
			'draw_divider': False,
			},
		]


def system_load(format='{avg:.1f}', threshold_good=1, threshold_bad=2):
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
	try:
		import psutil
	except ImportError:
		return None
	cpu_percent = int(psutil.cpu_percent(interval=measure_interval))
	return u'{0}%'.format(cpu_percent)


def network_load(interface='eth0', measure_interval=1, suffix='B/s', binary_prefix=False):
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
	return os.path.basename(os.environ.get('VIRTUAL_ENV', '')) or None


@memoize(60)
def email_imap_alert(username, password, server='imap.gmail.com', port=993, folder='INBOX'):
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
		state = self._convert_state(status)
		return {
			'state': state,
			'state_symbol': self.STATE_SYMBOLS.get(state),
			'album': info['xesam:album'],
			'artist': info['xesam:artist'][0],
			'title': info['xesam:title'],
			'total': self._convert_seconds(info['mpris:length'] / 1e6),
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
