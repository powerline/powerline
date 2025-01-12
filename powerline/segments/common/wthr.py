# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import json
import re
from collections import namedtuple

from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.threaded import KwThreadedSegment
from powerline.segments import with_docstring


_WeatherKey = namedtuple('Key', 'location_query weather_api_key')


# XXX Warning: module name must not be equal to the segment name as long as this
# segment is imported into powerline.segments.common module.


# Weather condition categories available at
# https://openweathermap.org/weather-conditions
weather_conditions_icons = {
	# group 2xx: thunderstorm
	'thunderstorm': 'STORM',

	# group 3xx: drizzle
	'drizzle':      'RAIN',

	# group 5xx: rain
	'rain':         'RAIN',

	# group 6xx: snow
	'snow':         'SNOW',

	# group 7xx: atmosphere
	'ash':          'FOG',
	'dust':         'FOG',
	'fog':          'FOG',
	'haze':         'FOG',
	'mist':         'FOG',
	'sand':         'FOG',
	'smoke':        'FOG',
	'squall':       'FOG',
	'tornado':      'TORNADO',

	# group 800: clear
	'clear':        'CLEAR',

	#group 80x: clouds
	'clouds':       'CLOUDS',

	'unknown':      'UKN',
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


class WeatherSegment(KwThreadedSegment):
	interval = 600
	default_location = None
	location_urls = {}
	weather_api_key = "fbc9549d91a5e4b26c15be0dbdac3460"

	@staticmethod
	def key(location_query=None, **kwargs):
		try:
			weather_api_key = kwargs["weather_api_key"]
		except KeyError:
			weather_api_key = WeatherSegment.weather_api_key
		return _WeatherKey(location_query, weather_api_key)

	def get_request_url(self, weather_key):
		try:
			return self.location_urls[weather_key]
		except KeyError:
			query_data = {
				"appid": weather_key.weather_api_key,
				"units": "metric",
			}
			location_query = weather_key.location_query
			if location_query is None:
				location_data = json.loads(urllib_read('https://freegeoip.app/json/'))
				query_data["lat"] = location_data["latitude"]
				query_data["lon"] = location_data["longitude"]
			else:
				query_data["q"] = location_query
			self.location_urls[location_query] = url = (
				"https://api.openweathermap.org/data/2.5/weather?" +
				urllib_urlencode(query_data))
			return url

	def compute_state(self, weather_key):
		url = self.get_request_url(weather_key)
		raw_response = urllib_read(url)
		if not raw_response:
			self.error('Failed to get response')
			return None

		response = json.loads(raw_response)
		try:
			weather = response['weather'][0]
			condition = weather['main'].lower()
			desc = re.sub(r'[^A-Za-z0-9]+', '_', weather['description'])
			temp = float(response['main']['temp'])
		except (KeyError, ValueError):
			self.exception('OpenWeatherMap returned malformed or unexpected response: {0}', repr(raw_response))
			return None

		try:
			icon_names = (desc, condition)
		except IndexError:
			icon_names = ('unknown',)
			self.error('Unknown condition code: {0}', condition_code)

		return (temp, icon_names)

	def render_one(self, weather, icons=None, unit='C', temp_format=None, temp_coldest=None, temp_hottest=None, **kwargs):
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
		if not temp_coldest:
			temp_coldest = temp_conversions[unit](-30)
		if not temp_hottest:
			temp_hottest = temp_conversions[unit](40)
		if converted_temp <= temp_coldest:
			gradient_level = 0
		elif converted_temp >= temp_hottest:
			gradient_level = 100
		else:
			gradient_level = (converted_temp - temp_coldest) * 100.0 / (temp_hottest - temp_coldest)
		groups = ['weather_condition_' + icon_name for icon_name in icon_names] + ['weather_conditions', 'weather']
		return [
			{
				'contents': icon + ' ',
				'highlight_groups': groups,
				'divider_highlight_group': 'background:divider',
			},
			{
				'contents': temp_format.format(temp=converted_temp),
				'highlight_groups': ['weather_temp_gradient', 'weather_temp', 'weather'],
				'divider_highlight_group': 'background:divider',
				'gradient_level': gradient_level,
			},
		]


weather = with_docstring(WeatherSegment(),
'''Return weather from OpenWeatherMaps.

Uses GeoIP lookup from https://freegeoip.app to automatically determine
your current location. This should be changed if you’re in a VPN or if your
IP address is registered at another location.

Icons can be overridden with a dict (see below). Names for the icons can be
either the main category name or the description with any non-alphanumeric
characters replaced with ``_``. Names should be lowercase.

See https://openweathermap.org/weather-conditions for weather condition
categories and descriptions.

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
Also uses ``weather_conditions_{condition}`` for all weather conditions supported by OpenWeatherMap.
''')
