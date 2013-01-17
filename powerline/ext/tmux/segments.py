# -*- coding: utf-8 -*-

import os

from powerline.lib import memoize

# Weather condition code descriptions available at http://developer.yahoo.com/weather/#codes
weather_conditions_codes = {
	u'〇': [25, 34],
	u'⚑': [24],
	u'☔': [5, 6, 8, 9, 10, 11, 12, 35, 40, 45, 47],
	u'☁': range(26, 30) + [44],
	u'❅': [7] + range(13, 18) + [41, 42, 43, 46],
	u'☈': range(0, 4) + range(37, 39),
	u'〰': range(19, 23),
	u'☼': [32, 36],
	u'☾': [31, 33],
}


def date(format='%Y-%m-%d'):
	from datetime import datetime
	return datetime.now().strftime(format)


@memoize(600, persistent=True)
def external_ip(query_url='http://icanhazip.com/'):
	import urllib2
	try:
		return urllib2.urlopen(query_url).read().strip()
	except urllib2.HTTPError:
		return


def system_load(format='{avg[0]:.1f}, {avg[1]:.1f}, {avg[2]:.1f}'):
	from multiprocessing import cpu_count
	averages = os.getloadavg()
	normalized = averages[1] / cpu_count()
	if normalized < 1:
		gradient = 'system_load_good'
	elif normalized < 2:
		gradient = 'system_load_bad'
	else:
		gradient = 'system_load_ugly'
	return {
		'contents': format.format(avg=averages),
		'highlight': [gradient, 'system_load']
	}


def uptime(format='{days:02d}d {hours:02d}h {minutes:02d}m'):
	# TODO: make this work with operating systems without /proc/uptime
	try:
		with open('/proc/uptime', 'r') as f:
			seconds = int(float(f.readline().split()[0]))
			minutes, seconds = divmod(seconds, 60)
			hours, minutes = divmod(minutes, 60)
			days, hours = divmod(hours, 24)
			return format.format(days=int(days), hours=hours, minutes=minutes)
	except IOError:
		pass


@memoize(600, persistent=True)
def weather(unit='c', location_query=None):
	import json
	import urllib
	import urllib2

	if not location_query:
		try:
			location = json.loads(urllib2.urlopen('http://freegeoip.net/json/' + external_ip()).read())
			location_query = ','.join([location['city'], location['region_name'], location['country_name']])
		except ValueError:
			return None
	query_data = {
		'q':
			'use "http://github.com/yql/yql-tables/raw/master/weather/weather.bylocation.xml" as we;'
			'select * from we where location="{0}" and unit="{1}"'.format(location_query, unit),
		'format': 'json'
	}
	url = 'http://query.yahooapis.com/v1/public/yql?' + urllib.urlencode(query_data)
	response = json.loads(urllib2.urlopen(url).read())
	condition = response['query']['results']['weather']['rss']['channel']['item']['condition']
	condition_code = int(condition['code'])
	icon = u'〇'
	for icon, codes in weather_conditions_codes.items():
		if condition_code in codes:
			break
	return u'{0}  {1}°{2}'.format(icon, condition['temp'], unit.upper())
