# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.lib.shell import asrun, run_cmd
from powerline.lib.unicode import out_u
from powerline.segments import Segment, with_docstring


STATE_SYMBOLS = {
	'fallback': '',
	'play': '>',
	'pause': '~',
	'stop': 'X',
}


def _convert_state(state):
	'''Guess player state'''
	state = state.lower()
	if 'play' in state:
		return 'play'
	if 'pause' in state:
		return 'pause'
	if 'stop' in state:
		return 'stop'
	return 'fallback'


def _convert_seconds(seconds):
	'''Convert seconds to minutes:seconds format'''
	return '{0:.0f}:{1:02.0f}'.format(*divmod(float(seconds), 60))


class PlayerSegment(Segment):
	def __call__(self, format='{state_symbol} {artist} - {title} ({total})', state_symbols=STATE_SYMBOLS, **kwargs):
		stats = {
			'state': 'fallback',
			'album': None,
			'artist': None,
			'title': None,
			'elapsed': None,
			'total': None,
		}
		func_stats = self.get_player_status(**kwargs)
		if not func_stats:
			return None
		stats.update(func_stats)
		stats['state_symbol'] = state_symbols.get(stats['state'])
		return [{
			'contents': format.format(**stats),
			'highlight_groups': ['player_' + (stats['state'] or 'fallback'), 'player'],
		}]

	def get_player_status(self, pl):
		pass

	def argspecobjs(self):
		for ret in super(PlayerSegment, self).argspecobjs():
			yield ret
		yield 'get_player_status', self.get_player_status

	def omitted_args(self, name, method):
		return (0,)


_common_args = '''
This player segment should be added like this:

.. code-block:: json

	{{
		"function": "powerline.segments.common.players.{0}",
		"name": "player"
	}}

(with additional ``"args": {{…}}`` if needed).

Highlight groups used: ``player_fallback`` or ``player``, ``player_play`` or ``player``, ``player_pause`` or ``player``, ``player_stop`` or ``player``.

:param str format:
	Format used for displaying data from player. Should be a str.format-like 
	string with the following keyword parameters:

	+------------+-------------------------------------------------------------+
	|Parameter   |Description                                                  |
	+============+=============================================================+
	|state_symbol|Symbol displayed for play/pause/stop states. There is also   |
	|            |“fallback” state used in case function failed to get player  |
	|            |state. For this state symbol is by default empty. All        |
	|            |symbols are defined in ``state_symbols`` argument.           |
	+------------+-------------------------------------------------------------+
	|album       |Album that is currently played.                              |
	+------------+-------------------------------------------------------------+
	|artist      |Artist whose song is currently played                        |
	+------------+-------------------------------------------------------------+
	|title       |Currently played composition.                                |
	+------------+-------------------------------------------------------------+
	|elapsed     |Composition duration in format M:SS (minutes:seconds).       |
	+------------+-------------------------------------------------------------+
	|total       |Composition length in format M:SS.                           |
	+------------+-------------------------------------------------------------+
:param dict state_symbols:
	Symbols used for displaying state. Must contain all of the following keys:

	========  ========================================================
	Key       Description
	========  ========================================================
	play      Displayed when player is playing.
	pause     Displayed when player is paused.
	stop      Displayed when player is not playing anything.
	fallback  Displayed if state is not one of the above or not known.
	========  ========================================================
'''


_player = with_docstring(PlayerSegment(), _common_args.format('_player'))


class CmusPlayerSegment(PlayerSegment):
	def get_player_status(self, pl):
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
		state = _convert_state(now_playing.get('status'))
		return {
			'state': state,
			'album': now_playing.get('album'),
			'artist': now_playing.get('artist'),
			'title': now_playing.get('title'),
			'elapsed': _convert_seconds(now_playing.get('position', 0)),
			'total': _convert_seconds(now_playing.get('duration', 0)),
		}


cmus = with_docstring(CmusPlayerSegment(),
('''Return CMUS player information

Requires cmus-remote command be acessible from $PATH.

{0}
''').format(_common_args.format('cmus')))


class MpdPlayerSegment(PlayerSegment):
	def get_player_status(self, pl, host='localhost', port=6600):
		try:
			import mpd
		except ImportError:
			now_playing = run_cmd(pl, [
				'mpc', 'current',
				'-f', '%album%\n%artist%\n%title%\n%time%',
				'-h', str(host),
				'-p', str(port)
			], strip=False)
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
				'elapsed': _convert_seconds(now_playing.get('elapsed', 0)),
				'total': _convert_seconds(now_playing.get('time', 0)),
			}


mpd = with_docstring(MpdPlayerSegment(),
('''Return Music Player Daemon information

Requires mpc command to be acessible from $PATH or ``mpd`` Python module.

{0}
:param str host:
	Host on which mpd runs.
:param int port:
	Port which should be connected to.
''').format(_common_args.format('mpd')))


try:
	import dbus
except ImportError:
	def _get_dbus_player_status(pl, player_name, **kwargs):
		pl.error('Could not add {0} segment: requires dbus module', player_name)
		return
else:
	def _get_dbus_player_status(pl, bus_name, player_path, iface_prop,
	                            iface_player, player_name='player'):
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
		album = info.get('xesam:album')
		title = info.get('xesam:title')
		artist = info.get('xesam:artist')
		state = _convert_state(status)
		if album:
			album = out_u(album)
		if title:
			title = out_u(title)
		if artist:
			artist = out_u(artist[0])
		return {
			'state': state,
			'album': album,
			'artist': artist,
			'title': title,
			'total': _convert_seconds(info.get('mpris:length') / 1e6),
		}


class DbusPlayerSegment(PlayerSegment):
	get_player_status = staticmethod(_get_dbus_player_status)


dbus_player = with_docstring(DbusPlayerSegment(),
('''Return generic dbus player state

Requires ``dbus`` python module. Only for players that support specific protocol 
 (e.g. like :py:func:`spotify` and :py:func:`clementine`).

{0}
:param str player_name:
	Player name. Used in error messages only.
:param str bus_name:
	Dbus bus name.
:param str player_path:
	Path to the player on the given bus.
:param str iface_prop:
	Interface properties name for use with dbus.Interface.
:param str iface_player:
	Player name.
''').format(_common_args.format('dbus_player')))


class SpotifyDbusPlayerSegment(PlayerSegment):
	def get_player_status(self, pl):
		return _get_dbus_player_status(
			pl=pl,
			player_name='Spotify',
			bus_name='com.spotify.qt',
			player_path='/',
			iface_prop='org.freedesktop.DBus.Properties',
			iface_player='org.freedesktop.MediaPlayer2',
		)


spotify_dbus = with_docstring(SpotifyDbusPlayerSegment(),
('''Return spotify player information

Requires ``dbus`` python module.

{0}
''').format(_common_args.format('spotify_dbus')))


class SpotifyAppleScriptPlayerSegment(PlayerSegment):
	def get_player_status(self, pl):
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
		state = _convert_state(spotify_status[0])
		if state == 'stop':
			return None
		return {
			'state': state,
			'album': spotify_status[1],
			'artist': spotify_status[2],
			'title': spotify_status[3],
			'total': _convert_seconds(int(spotify_status[4]))
		}


spotify_apple_script = with_docstring(SpotifyAppleScriptPlayerSegment(),
('''Return spotify player information

Requires ``osascript`` available in $PATH.

{0}
''').format(_common_args.format('spotify_apple_script')))


if 'dbus' in globals() or not sys.platform.startswith('darwin'):
	spotify = spotify_dbus
	_old_name = 'spotify_dbus'
else:
	spotify = spotify_apple_script
	_old_name = 'spotify_apple_script'


spotify = with_docstring(spotify, spotify.__doc__.replace(_old_name, 'spotify'))


class ClementinePlayerSegment(PlayerSegment):
	def get_player_status(self, pl):
		return _get_dbus_player_status(
			pl=pl,
			player_name='Clementine',
			bus_name='org.mpris.MediaPlayer2.clementine',
			player_path='/org/mpris/MediaPlayer2',
			iface_prop='org.freedesktop.DBus.Properties',
			iface_player='org.mpris.MediaPlayer2.Player',
		)


clementine = with_docstring(ClementinePlayerSegment(),
('''Return clementine player information

Requires ``dbus`` python module.

{0}
''').format(_common_args.format('clementine')))


class RhythmboxPlayerSegment(PlayerSegment):
	def get_player_status(self, pl):
		now_playing = run_cmd(pl, [
			'rhythmbox-client',
			'--no-start', '--no-present',
			'--print-playing-format', '%at\n%aa\n%tt\n%te\n%td'
		], strip=False)
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


rhythmbox = with_docstring(RhythmboxPlayerSegment(),
('''Return rhythmbox player information

Requires ``rhythmbox-client`` available in $PATH.

{0}
''').format(_common_args.format('rhythmbox')))


class RDIOPlayerSegment(PlayerSegment):
	def get_player_status(self, pl):
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
		now_playing = now_playing.split(status_delimiter)
		if len(now_playing) != 6:
			return
		state = _convert_state(now_playing[5])
		total = _convert_seconds(now_playing[4])
		elapsed = _convert_seconds(float(now_playing[3]) * float(now_playing[4]) / 100)
		return {
			'title': now_playing[0],
			'artist': now_playing[1],
			'album': now_playing[2],
			'elapsed': elapsed,
			'total': total,
			'state': state,
		}


rdio = with_docstring(RDIOPlayerSegment(),
('''Return rdio player information

Requires ``osascript`` available in $PATH.

{0}
''').format(_common_args.format('rdio')))
