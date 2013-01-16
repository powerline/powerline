# -*- coding: utf-8 -*-

import cPickle as pickle
import functools
import os
import tempfile
import time


class memoize(object):
	'''Memoization decorator with timeout.'''
	_cache = {}

	def __init__(self, timeout, additional_key=None, persistent=False, persistent_file=None):
		self.timeout = timeout
		self.additional_key = additional_key
		self.persistent = persistent
		self.persistent_file = persistent_file or os.path.join(tempfile.gettempdir(), 'powerline-cache')

	def __call__(self, func):
		@functools.wraps(func)
		def decorated_function(*args, **kwargs):
			if self.additional_key:
				key = (func.__name__, args, tuple(kwargs.items()), self.additional_key())
			else:
				key = (func.__name__, args, tuple(kwargs.items()))
			if self.persistent:
				try:
					with open(self.persistent_file, 'rb') as fileobj:
						self._cache = pickle.load(fileobj)
				except (IOError, EOFError):
					pass
			cached = self._cache.get(key, None)
			if cached is None or time.time() - cached['time'] > self.timeout:
				cached = self._cache[key] = {
					'result': func(*args, **kwargs),
					'time': time.time(),
					}
				if self.persistent:
					try:
						with open(self.persistent_file, 'wb') as fileobj:
							pickle.dump(self._cache, fileobj)
					except IOError:
						# Unable to write to file
						pass
					except TypeError:
						# Unable to pickle function result
						pass
			return cached['result']
		return decorated_function
