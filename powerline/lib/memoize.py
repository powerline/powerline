# -*- coding: utf-8 -*-

import time


class memoize(object):
	'''Memoization decorator with timeout.'''
	_cache = {}

	def __init__(self, timeout, additional_key=None):
		self.timeout = timeout
		self.additional_key = additional_key

	def __call__(self, func):
		def decorated_function(*args, **kwargs):
			if self.additional_key:
				key = (func.__name__, args, tuple(kwargs.items()), self.additional_key())
			else:
				key = (func.__name__, args, tuple(kwargs.items()))
			cached = self._cache.get(key, None)
			if cached is None or time.time() - cached['time'] > self.timeout:
				cached = self._cache[key] = {
					'result': func(*args, **kwargs),
					'time': time.time(),
					}
			return cached['result']
		return decorated_function
