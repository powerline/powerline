# -*- coding: utf-8 -*-

import os
import re
import socket

from powerline.lib.vcs import guess
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


def hostname():
	if not os.environ.get('SSH_CLIENT'):
		return None
	return socket.gethostname()


def user():
	user = os.environ.get('USER')
	euid = os.geteuid()
	return {
		'contents': user,
		'highlight': 'user' if euid != 0 else ['superuser', 'user'],
		}


def branch():
	repo = guess(os.path.abspath(os.getcwd()))
	if repo:
		return repo.branch()
	return None


def cwd(dir_shorten_len=None, dir_limit_depth=None):
	cwd = os.getcwdu()
	home = os.environ.get('HOME')
	if home:
		cwd = re.sub('^' + re.escape(home), '~', cwd, 1)
	cwd_split = cwd.split(os.sep)
	cwd_split_len = len(cwd_split)
	if cwd_split_len > dir_limit_depth + 1:
		del(cwd_split[0:-dir_limit_depth])
		cwd_split.insert(0, u'⋯')
	cwd = [i[0:dir_shorten_len] if dir_shorten_len and i else i for i in cwd_split[:-1]] + [cwd_split[-1]]
	cwd = os.path.join(*cwd)
	return cwd


def date(format='%Y-%m-%d'):
	from datetime import datetime
	return datetime.now().strftime(format)


@memoize(600, persistent=True)
def external_ip(query_url='http://ipv4.icanhazip.com/'):
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


def network_load(interface='eth0', measure_interval=1, suffix='B/s', binary_prefix=False):
	import time
	from powerline.lib import humanize_bytes

	def get_bytes():
		try:
			with open('/sys/class/net/{interface}/statistics/rx_bytes'.format(interface=interface), 'rb') as file_obj:
				rx = int(file_obj.read())
			with open('/sys/class/net/{interface}/statistics/tx_bytes'.format(interface=interface), 'rb') as file_obj:
				tx = int(file_obj.read())
			return (rx, tx)
		except IOError:
			return (0, 0)

	b1 = get_bytes()
	time.sleep(measure_interval)
	b2 = get_bytes()
	return u'⬇ {rx_diff} ⬆ {tx_diff}'.format(
		rx_diff=humanize_bytes((b2[0] - b1[0]) / measure_interval, suffix, binary_prefix),
		tx_diff=humanize_bytes((b2[1] - b1[1]) / measure_interval, suffix, binary_prefix),
		)
