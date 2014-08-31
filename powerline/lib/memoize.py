# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

from functools import wraps

from powerline.lib.monotonic import monotonic


def default_cache_key(**kwargs):
	return frozenset(kwargs.items())


class memoize(object):
	'''Memoization decorator with timeout.'''
	def __init__(self, timeout, cache_key=default_cache_key, cache_reg_func=None):
		self.timeout = timeout
		self.cache_key = cache_key
		self.cache = {}
		self.cache_reg_func = cache_reg_func

	def __call__(self, func):
		@wraps(func)
		def decorated_function(**kwargs):
			if self.cache_reg_func:
				self.cache_reg_func(self.cache)
				self.cache_reg_func = None

			key = self.cache_key(**kwargs)
			try:
				cached = self.cache.get(key, None)
			except TypeError:
				return func(**kwargs)
			# Handle case when time() appears to be less then cached['time'] due 
			# to clock updates. Not applicable for monotonic clock, but this 
			# case is currently rare.
			if cached is None or not (cached['time'] < monotonic() < cached['time'] + self.timeout):
				cached = self.cache[key] = {
					'result': func(**kwargs),
					'time': monotonic(),
				}
			return cached['result']
		return decorated_function
