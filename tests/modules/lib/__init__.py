# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys
import types


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
		elif query_url.startswith('http://ipv6.icanhazip.com'):
			return '2001:4801:7818:6:abc5:ba2c:ff10:275f'

	elif query_url.startswith('https://freegeoip.app/json/'):
		return '{"ip":"82.145.55.16","country_code":"DE","country_name":"Germany","region_code":"NI","region_name":"Lower Saxony","city":"Meppen","zip_code":"49716","time_zone":"Europe/Berlin","latitude":52.6833,"longitude":7.3167,"metro_code":0}'
	elif query_url.startswith('https://api.openweathermap.org/data/2.5/'):
		if 'Meppen' in query_url or '52.6833' in query_url:
			return r'{"coord":{"lon":7.29,"lat":52.69},"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"base":"stations","main":{"temp":293.15,"feels_like":295.16,"temp_min":293.15,"temp_max":295.37,"pressure":1018,"humidity":77},"visibility":10000,"wind":{"speed":1.12,"deg":126},"clouds":{"all":0},"dt":1600196220,"sys":{"type":1,"id":1871,"country":"DE","sunrise":1600146332,"sunset":1600191996},"timezone":7200,"id":2871845,"name":"Meppen","cod":200}'
		elif 'Moscow' in query_url:
			return r'{"coord":{"lon":37.62,"lat":55.75},"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}],"base":"stations","main":{"temp":283.15,"feels_like":280.78,"temp_min":283.15,"temp_max":284.26,"pressure":1019,"humidity":71},"visibility":10000,"wind":{"speed":3,"deg":330},"clouds":{"all":0},"dt":1600196224,"sys":{"type":1,"id":9029,"country":"RU","sunrise":1600138909,"sunset":1600184863},"timezone":10800,"id":524901,"name":"Moscow","cod":200}'

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
	try:
		module = types.ModuleType(name)
	except TypeError:
		import imp
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
