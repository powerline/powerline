# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.lib.shell import asrun, run_cmd
from powerline.lib.unicode import out_u
from powerline.segments import Segment


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

		For the information we are looking for we don’t really care if we’re on
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
			self.exception('Could not add {0} segment: requires dbus module', player_name)
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
		album = out_u(info.get('xesam:album'))
		title = out_u(info.get('xesam:title'))
		artist = info.get('xesam:artist')
		state = self._convert_state(status)
		if artist:
			artist = out_u(artist[0])
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
