# vim:fileencoding=utf-8:noet
import imp
import sys
import os


class Args(object):
	theme_option = None
	config = None
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
	elif query_url.startswith('http://freegeoip.net/json/'):
		return '{"city": "Meppen", "region_code": "06", "region_name": "Niedersachsen", "areacode": "", "ip": "82.145.55.16", "zipcode": "49716", "longitude": 7.3167, "country_name": "Germany", "country_code": "DE", "metrocode": "", "latitude": 52.6833}'
	elif query_url.startswith('http://query.yahooapis.com/v1/public/'):
		return '{"query":{"count":1,"created":"2013-03-02T13:20:22Z","lang":"en-US","results":{"weather":{"rss":{"version":"2.0","geo":"http://www.w3.org/2003/01/geo/wgs84_pos#","yweather":"http://xml.weather.yahoo.com/ns/rss/1.0","channel":{"title":"Yahoo! Weather - Russia, RU","link":"http://us.rd.yahoo.com/dailynews/rss/weather/Russia__RU/*http://weather.yahoo.com/forecast/RSXX1511_c.html","description":"Yahoo! Weather for Russia, RU","language":"en-us","lastBuildDate":"Sat, 02 Mar 2013 4:58 pm MSK","ttl":"60","location":{"city":"Russia","country":"Russia","region":""},"units":{"distance":"km","pressure":"mb","speed":"km/h","temperature":"C"},"wind":{"chill":"-11","direction":"0","speed":""},"atmosphere":{"humidity":"94","pressure":"1006.1","rising":"0","visibility":""},"astronomy":{"sunrise":"10:04 am","sunset":"7:57 pm"},"image":{"title":"Yahoo! Weather","width":"142","height":"18","link":"http://weather.yahoo.com","url":"http://l.yimg.com/a/i/brand/purplelogo//uh/us/news-wea.gif"},"item":{"title":"Conditions for Russia, RU at 4:58 pm MSK","lat":"59.45","long":"108.83","link":"http://us.rd.yahoo.com/dailynews/rss/weather/Russia__RU/*http://weather.yahoo.com/forecast/RSXX1511_c.html","pubDate":"Sat, 02 Mar 2013 4:58 pm MSK","condition":{"code":"30","date":"Sat, 02 Mar 2013 4:58 pm MSK","temp":"-11","text":"Partly Cloudy"},"description":"<img src=\"http://l.yimg.com/a/i/us/we/52/30.gif\"/><br />\n<b>Current Conditions:</b><br />\nPartly Cloudy, -11 C<BR />\n<BR /><b>Forecast:</b><BR />\nSat - Partly Cloudy. High: -9 Low: -19<br />\nSun - Partly Cloudy. High: -12 Low: -18<br />\n<br />\n<a href=\"http://us.rd.yahoo.com/dailynews/rss/weather/Russia__RU/*http://weather.yahoo.com/forecast/RSXX1511_c.html\">Full Forecast at Yahoo! Weather</a><BR/><BR/>\n(provided by <a href=\"http://www.weather.com\" >The Weather Channel</a>)<br/>","forecast":[{"code":"29","date":"2 Mar 2013","day":"Sat","high":"-9","low":"-19","text":"Partly Cloudy"},{"code":"30","date":"3 Mar 2013","day":"Sun","high":"-12","low":"-18","text":"Partly Cloudy"}],"guid":{"isPermaLink":"false","content":"RSXX1511_2013_03_03_7_00_MSK"}}}}}}}}'
	else:
		raise NotImplementedError


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


class ModuleAttrReplace(object):
	def __init__(self, module, attr, new):
		self.module = module
		self.attr = attr
		self.new = new

	def __enter__(self):
		try:
			self.old = getattr(self.module, self.attr)
		except AttributeError:
			pass
		setattr(self.module, self.attr, self.new)

	def __exit__(self, *args):
		try:
			setattr(self.module, self.attr, self.old)
		except AttributeError:
			delattr(self.module, self.attr)


replace_module_attr = ModuleAttrReplace


def replace_module_module(module, name, **kwargs):
	return replace_module_attr(module, name, new_module(name, **kwargs))


class EnvReplace(object):
	def __init__(self, name, new):
		self.name = name
		self.new = new

	def __enter__(self):
		self.old = os.environ.get(self.name)
		os.environ[self.name] = self.new

	def __exit__(self, *args):
		if self.old is None:
			try:
				os.environ.pop(self.name)
			except KeyError:
				pass
		else:
			os.environ[self.name] = self.old


replace_env = EnvReplace
