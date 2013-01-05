# -*- coding: utf-8 -*-

import time


class memoize(object):
	'''Memoization decorator with timout.

	http://code.activestate.com/recipes/325905-memoize-decorator-with-timeout/
	'''
	_caches = {}
	_timeouts = {}

	def __init__(self, timeout, additional_key=None):
		self.timeout = timeout
		self.additional_key = additional_key

	def collect(self):
		'''Clear cache of results which have timed out.
		'''
		for func in self._caches:
			cache = {}
			for key in self._caches[func]:
				if (time.time() - self._caches[func][key][1]) < self._timeouts[func]:
					cache[key] = self._caches[func][key]
			self._caches[func] = cache

	def __call__(self, f):
		self.cache = self._caches[f] = {}
		self._timeouts[f] = self.timeout

		def func(*args, **kwargs):
			kw = kwargs.items()
			kw.sort()
			if self.additional_key:
				key = (args, tuple(kw), self.additional_key())
			else:
				key = (args, tuple(kw))
			try:
				v = self.cache[key]
				if (time.time() - v[1]) > self.timeout:
					raise KeyError
			except KeyError:
				v = self.cache[key] = f(*args, **kwargs), time.time()
			return v[0]
		func.func_name = f.func_name

		return func
