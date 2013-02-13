# -*- coding: utf-8 -*-

from functools import wraps
import time


def default_cache_key(**kwargs):
	return frozenset(kwargs.items())


class memoize(object):
	'''Memoization decorator with timeout.'''
	_cache = {}

	def __init__(self, timeout, cache_key=default_cache_key):
		self.timeout = timeout
		self.cache_key = cache_key

	def __call__(self, func):
		@wraps(func)
		def decorated_function(**kwargs):
			key = (func, self.cache_key(**kwargs))
			try:
				cached = self._cache.get(key, None)
			except TypeError:
				return func(**kwargs)
			if cached is None or time.time() - cached['time'] > self.timeout:
				cached = self._cache[key] = {
					'result': func(**kwargs),
					'time': time.time(),
					}
			return cached['result']
		return decorated_function
