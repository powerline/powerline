# -*- coding: utf-8 -*-

import time


class memoize(object):
	'''Memoization decorator with timout.

	http://code.activestate.com/recipes/325905-memoize-decorator-with-timeout/
	'''
	_caches = {}
	_timeouts = {}

	def __init__(self, timeout):
		self.timeout = timeout

	def collect(self):
		'''Clear cache of results which have timed out.
		'''
		for func in self._caches:
			cache = {}
			for key in self._caches[func]:
				if (time.clock() - self._caches[func][key][1]) < self._timeouts[func]:
					cache[key] = self._caches[func][key]
			self._caches[func] = cache

	def __call__(self, f):
		self.cache = self._caches[f] = {}
		self._timeouts[f] = self.timeout

		def func(*args, **kwargs):
			kw = kwargs.items()
			kw.sort()
			key = (args, tuple(kw))
			try:
				v = self.cache[key]
				if (time.clock() - v[1]) > self.timeout:
					raise KeyError
			except KeyError:
				v = self.cache[key] = f(*args, **kwargs), time.clock()
			return v[0]
		func.func_name = f.func_name

		return func
