# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import imp
import sys


class Pl(object):
	def __init__(self):
		self.exceptions = []
		self.errors = []
		self.warns = []
		self.debugs = []
		self.infos = []
		self.prefix = None
		self.use_daemon_threads = True

	for meth in ('error', 'warn', 'debug', 'exception', 'info'):
		exec((
			'def {0}(self, msg, *args, **kwargs):\n'
			'	self.{0}s.append((kwargs.get("prefix") or self.prefix, msg, args, kwargs))\n'
		).format(meth))

	def __nonzero__(self):
		return bool(self.exceptions or self.errors or self.warns)

	__bool__ = __nonzero__


class Args(object):
	theme_override = {}
	config_override = {}
	config_path = None
	ext = ['shell']
	renderer_module = None

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


def urllib_read(query_url):
	if query_url.startswith('http://ipv'):
		if query_url.startswith('http://ipv4.icanhazip.com'):
			return '127.0.0.1'
		elif query_url.startswith('http://ipv4.icanhazip.com'):
			return '2001:4801:7818:6:abc5:ba2c:ff10:275f'
	elif query_url.startswith('http://geoip.nekudo.com/api/'):
		return '{"city":"Meppen","country":{"name":"Germany", "code":"DE"},"location":{"accuracy_radius":100,"latitude":52.6833,"longitude":7.3167,"time_zone":"Europe\/Berlin"},"ip":"82.145.55.16"}'
	elif query_url.startswith('http://query.yahooapis.com/v1/public/'):
		if 'Meppen' in query_url:
			return r'{"query":{"count":1,"created":"2016-05-13T19:43:18Z","lang":"en-US","results":{"channel":{"units":{"distance":"mi","pressure":"in","speed":"mph","temperature":"C"},"title":"Yahoo! Weather - Meppen, NI, DE","link":"http://us.rd.yahoo.com/dailynews/rss/weather/Country__Country/*https://weather.yahoo.com/country/state/city-674836/","description":"Yahoo! Weather for Meppen, NI, DE","language":"en-us","lastBuildDate":"Fri, 13 May 2016 09:43 PM CEST","ttl":"60","location":{"city":"Meppen","country":"Germany","region":" NI"},"wind":{"chill":"55","direction":"350","speed":"25"},"atmosphere":{"humidity":"57","pressure":"1004.0","rising":"0","visibility":"16.1"},"astronomy":{"sunrise":"5:35 am","sunset":"9:21 pm"},"image":{"title":"Yahoo! Weather","width":"142","height":"18","link":"http://weather.yahoo.com","url":"http://l.yimg.com/a/i/brand/purplelogo//uh/us/news-wea.gif"},"item":{"title":"Conditions for Meppen, NI, DE at 08:00 PM CEST","lat":"52.68993","long":"7.29115","link":"http://us.rd.yahoo.com/dailynews/rss/weather/Country__Country/*https://weather.yahoo.com/country/state/city-674836/","pubDate":"Fri, 13 May 2016 08:00 PM CEST","condition":{"code":"23","date":"Fri, 13 May 2016 08:00 PM CEST","temp":"14","text":"Breezy"},"forecast":[{"code":"30","date":"13 May 2016","day":"Fri","high":"71","low":"48","text":"Partly Cloudy"},{"code":"28","date":"14 May 2016","day":"Sat","high":"54","low":"44","text":"Mostly Cloudy"},{"code":"11","date":"15 May 2016","day":"Sun","high":"55","low":"43","text":"Showers"},{"code":"28","date":"16 May 2016","day":"Mon","high":"54","low":"42","text":"Mostly Cloudy"},{"code":"28","date":"17 May 2016","day":"Tue","high":"57","low":"43","text":"Mostly Cloudy"},{"code":"12","date":"18 May 2016","day":"Wed","high":"62","low":"45","text":"Rain"},{"code":"28","date":"19 May 2016","day":"Thu","high":"63","low":"48","text":"Mostly Cloudy"},{"code":"28","date":"20 May 2016","day":"Fri","high":"67","low":"50","text":"Mostly Cloudy"},{"code":"30","date":"21 May 2016","day":"Sat","high":"71","low":"50","text":"Partly Cloudy"},{"code":"30","date":"22 May 2016","day":"Sun","high":"74","low":"54","text":"Partly Cloudy"}],"description":"<![CDATA[<img src=\"http://l.yimg.com/a/i/us/we/52/23.gif\"/>\n<BR />\n<b>Current Conditions:</b>\n<BR />Breezy\n<BR />\n<BR />\n<b>Forecast:</b>\n<BR /> Fri - Partly Cloudy. High: 71Low: 48\n<BR /> Sat - Mostly Cloudy. High: 54Low: 44\n<BR /> Sun - Showers. High: 55Low: 43\n<BR /> Mon - Mostly Cloudy. High: 54Low: 42\n<BR /> Tue - Mostly Cloudy. High: 57Low: 43\n<BR />\n<BR />\n<a href=\"http://us.rd.yahoo.com/dailynews/rss/weather/Country__Country/*https://weather.yahoo.com/country/state/city-674836/\">Full Forecast at Yahoo! Weather</a>\n<BR />\n<BR />\n(provided by <a href=\"http://www.weather.com\" >The Weather Channel</a>)\n<BR />\n]]>","guid":{"isPermaLink":"false"}}}}}}'
		elif 'Moscow' in query_url:
			return r'{"query":{"count":1,"created":"2016-05-13T19:47:01Z","lang":"en-US","results":{"channel":{"units":{"distance":"mi","pressure":"in","speed":"mph","temperature":"C"},"title":"Yahoo! Weather - Moscow, Moscow Federal City, RU","link":"http://us.rd.yahoo.com/dailynews/rss/weather/Country__Country/*https://weather.yahoo.com/country/state/city-2122265/","description":"Yahoo! Weather for Moscow, Moscow Federal City, RU","language":"en-us","lastBuildDate":"Fri, 13 May 2016 10:47 PM MSK","ttl":"60","location":{"city":"Moscow","country":"Russia","region":" Moscow Federal City"},"wind":{"chill":"45","direction":"80","speed":"11"},"atmosphere":{"humidity":"52","pressure":"993.0","rising":"0","visibility":"16.1"},"astronomy":{"sunrise":"4:19 am","sunset":"8:34 pm"},"image":{"title":"Yahoo! Weather","width":"142","height":"18","link":"http://weather.yahoo.com","url":"http://l.yimg.com/a/i/brand/purplelogo//uh/us/news-wea.gif"},"item":{"title":"Conditions for Moscow, Moscow Federal City, RU at 09:00 PM MSK","lat":"55.741638","long":"37.605061","link":"http://us.rd.yahoo.com/dailynews/rss/weather/Country__Country/*https://weather.yahoo.com/country/state/city-2122265/","pubDate":"Fri, 13 May 2016 09:00 PM MSK","condition":{"code":"33","date":"Fri, 13 May 2016 09:00 PM MSK","temp":"9","text":"Mostly Clear"},"forecast":[{"code":"30","date":"13 May 2016","day":"Fri","high":"62","low":"41","text":"Partly Cloudy"},{"code":"30","date":"14 May 2016","day":"Sat","high":"64","low":"43","text":"Partly Cloudy"},{"code":"30","date":"15 May 2016","day":"Sun","high":"63","low":"44","text":"Partly Cloudy"},{"code":"12","date":"16 May 2016","day":"Mon","high":"60","low":"47","text":"Rain"},{"code":"12","date":"17 May 2016","day":"Tue","high":"64","low":"48","text":"Rain"},{"code":"28","date":"18 May 2016","day":"Wed","high":"67","low":"48","text":"Mostly Cloudy"},{"code":"12","date":"19 May 2016","day":"Thu","high":"68","low":"49","text":"Rain"},{"code":"39","date":"20 May 2016","day":"Fri","high":"66","low":"50","text":"Scattered Showers"},{"code":"39","date":"21 May 2016","day":"Sat","high":"69","low":"49","text":"Scattered Showers"},{"code":"30","date":"22 May 2016","day":"Sun","high":"73","low":"50","text":"Partly Cloudy"}],"description":"<![CDATA[<img src=\"http://l.yimg.com/a/i/us/we/52/33.gif\"/>\n<BR />\n<b>Current Conditions:</b>\n<BR />Mostly Clear\n<BR />\n<BR />\n<b>Forecast:</b>\n<BR /> Fri - Partly Cloudy. High: 62Low: 41\n<BR /> Sat - Partly Cloudy. High: 64Low: 43\n<BR /> Sun - Partly Cloudy. High: 63Low: 44\n<BR /> Mon - Rain. High: 60Low: 47\n<BR /> Tue - Rain. High: 64Low: 48\n<BR />\n<BR />\n<a href=\"http://us.rd.yahoo.com/dailynews/rss/weather/Country__Country/*https://weather.yahoo.com/country/state/city-2122265/\">Full Forecast at Yahoo! Weather</a>\n<BR />\n<BR />\n(provided by <a href=\"http://www.weather.com\" >The Weather Channel</a>)\n<BR />\n]]>","guid":{"isPermaLink":"false"}}}}}}'
	else:
		raise NotImplementedError


class Process(object):
	def __init__(self, output, err):
		self.output = output
		self.err = err

	def communicate(self):
		return self.output, self.err


class ModuleReplace(object):
	def __init__(self, name, new):
		self.name = name
		self.new = new

	def __enter__(self):
		self.old = sys.modules.get(self.name)
		if not self.old:
			try:
				self.old = __import__(self.name)
			except ImportError:
				pass
		sys.modules[self.name] = self.new

	def __exit__(self, *args):
		if self.old:
			sys.modules[self.name] = self.old
		else:
			sys.modules.pop(self.name)


def replace_module(name, new=None, **kwargs):
	if not new:
		new = new_module(name, **kwargs)
	return ModuleReplace(name, new)


def new_module(name, **kwargs):
	module = imp.new_module(name)
	for k, v in kwargs.items():
		setattr(module, k, v)
	return module


class AttrReplace(object):
	def __init__(self, obj, *args):
		self.obj = obj
		self.attrs = args[::2]
		self.new = args[1::2]

	def __enter__(self):
		self.old = {}
		for i, attr in enumerate(self.attrs):
			try:
				self.old[i] = getattr(self.obj, attr)
			except AttributeError:
				pass
		for attr, new in zip(self.attrs, self.new):
			setattr(self.obj, attr, new)

	def __exit__(self, *args):
		for i, attr in enumerate(self.attrs):
			try:
				old = self.old[i]
			except KeyError:
				delattr(self.obj, attr)
			else:
				setattr(self.obj, attr, old)


replace_attr = AttrReplace


def replace_module_module(module, name, **kwargs):
	return replace_attr(module, name, new_module(name, **kwargs))


class ItemReplace(object):
	def __init__(self, d, key, new, r=None):
		self.key = key
		self.new = new
		self.d = d
		self.r = r

	def __enter__(self):
		self.old = self.d.get(self.key)
		self.d[self.key] = self.new
		return self.r

	def __exit__(self, *args):
		if self.old is None:
			try:
				self.d.pop(self.key)
			except KeyError:
				pass
		else:
			self.d[self.key] = self.old


def replace_item(d, key, new):
	return ItemReplace(d, key, new, d)


def replace_env(key, new, environ=None, **kwargs):
	r = kwargs.copy()
	r['environ'] = environ or {}
	return ItemReplace(r['environ'], key, new, r)


class PowerlineSingleTest(object):
	def __init__(self, suite, name):
		self.suite = suite
		self.name = name

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is not None:
			self.exception('Exception while running test: {0!r}'.format(
				exc_value))

	def fail(self, message, allow_failure=False):
		return self.suite.fail(self.name, message, allow_failure)

	def exception(self, message, allow_failure=False):
		return self.suite.exception(self.name, message, allow_failure)
