# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import json
import codecs

from copy import deepcopy
from threading import Event, Lock
from collections import defaultdict

from powerline.lib.threaded import MultiRunnedThread
from powerline.lib.watcher import create_file_watcher


def open_file(path):
	return codecs.open(path, encoding='utf-8')


def load_json_config(config_file_path, load=json.load, open_file=open_file):
	with open_file(config_file_path) as config_file_fp:
		return load(config_file_fp)


class DummyWatcher(object):
	def __call__(self, *args, **kwargs):
		return False

	def watch(self, *args, **kwargs):
		pass


class DeferredWatcher(object):
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs
		self.calls = []

	def __call__(self, *args, **kwargs):
		self.calls.append(('__call__', args, kwargs))

	def watch(self, *args, **kwargs):
		self.calls.append(('watch', args, kwargs))

	def unwatch(self, *args, **kwargs):
		self.calls.append(('unwatch', args, kwargs))

	def transfer_calls(self, watcher):
		for attr, args, kwargs in self.calls:
			getattr(watcher, attr)(*args, **kwargs)


class ConfigLoader(MultiRunnedThread):
	def __init__(self, shutdown_event=None, watcher=None, watcher_type=None, load=load_json_config, run_once=False):
		super(ConfigLoader, self).__init__()
		self.shutdown_event = shutdown_event or Event()
		if run_once:
			self.watcher = DummyWatcher()
			self.watcher_type = 'dummy'
		else:
			self.watcher = watcher or DeferredWatcher()
			if watcher:
				if not watcher_type:
					raise ValueError('When specifying watcher you must also specify watcher type')
				self.watcher_type = watcher_type
			else:
				self.watcher_type = 'deferred'
		self._load = load

		self.pl = None
		self.interval = None

		self.lock = Lock()

		self.watched = defaultdict(set)
		self.missing = defaultdict(set)
		self.loaded = {}

	def set_watcher(self, watcher_type, force=False):
		if watcher_type == self.watcher_type:
			return
		watcher = create_file_watcher(self.pl, watcher_type)
		with self.lock:
			if self.watcher_type == 'deferred':
				self.watcher.transfer_calls(watcher)
			self.watcher = watcher
			self.watcher_type = watcher_type

	def set_pl(self, pl):
		self.pl = pl

	def set_interval(self, interval):
		self.interval = interval

	def register(self, function, path):
		'''Register function that will be run when file changes.

		:param function function:
			Function that will be called when file at the given path changes.
		:param str path:
			Path that will be watched for.
		'''
		with self.lock:
			self.watched[path].add(function)
			self.watcher.watch(path)

	def register_missing(self, condition_function, function, key):
		'''Register any function that will be called with given key each 
		interval seconds (interval is defined at __init__). Its result is then 
		passed to ``function``, but only if the result is true.

		:param function condition_function:
			Function which will be called each ``interval`` seconds. All 
			exceptions from it will be logged and ignored. IOError exception 
			will be ignored without logging.
		:param function function:
			Function which will be called if condition_function returns 
			something that is true. Accepts result of condition_function as an 
			argument.
		:param str key:
			Any value, it will be passed to condition_function on each call.

		Note: registered functions will be automatically removed if 
		condition_function results in something true.
		'''
		with self.lock:
			self.missing[key].add((condition_function, function))

	def unregister_functions(self, removed_functions):
		'''Unregister files handled by these functions.

		:param set removed_functions:
			Set of functions previously passed to ``.register()`` method.
		'''
		with self.lock:
			for path, functions in list(self.watched.items()):
				functions -= removed_functions
				if not functions:
					self.watched.pop(path)
					self.loaded.pop(path, None)

	def unregister_missing(self, removed_functions):
		'''Unregister files handled by these functions.

		:param set removed_functions:
			Set of pairs (2-tuples) representing ``(condition_function, 
			function)`` function pairs previously passed as an arguments to 
			``.register_missing()`` method.
		'''
		with self.lock:
			for key, functions in list(self.missing.items()):
				functions -= removed_functions
				if not functions:
					self.missing.pop(key)

	def load(self, path):
		try:
			# No locks: GIL does what we need
			return deepcopy(self.loaded[path])
		except KeyError:
			r = self._load(path)
			self.loaded[path] = deepcopy(r)
			return r

	def update(self):
		toload = []
		with self.lock:
			for path, functions in self.watched.items():
				for function in functions:
					try:
						modified = self.watcher(path)
					except OSError as e:
						modified = True
						self.exception('Error while running watcher for path {0}: {1}', path, str(e))
					else:
						if modified:
							toload.append(path)
					if modified:
						function(path)
		with self.lock:
			for key, functions in list(self.missing.items()):
				for condition_function, function in list(functions):
					try:
						path = condition_function(key)
					except IOError:
						pass
					except Exception as e:
						self.exception('Error while running condition function for key {0}: {1}', key, str(e))
					else:
						if path:
							toload.append(path)
							function(path)
							functions.remove((condition_function, function))
				if not functions:
					self.missing.pop(key)
		for path in toload:
			try:
				self.loaded[path] = deepcopy(self._load(path))
			except Exception as e:
				self.exception('Error while loading {0}: {1}', path, str(e))
				try:
					self.loaded.pop(path)
				except KeyError:
					pass
				try:
					self.loaded.pop(path)
				except KeyError:
					pass

	def run(self):
		while self.interval is not None and not self.shutdown_event.is_set():
			self.update()
			self.shutdown_event.wait(self.interval)

	def exception(self, msg, *args, **kwargs):
		if self.pl:
			self.pl.exception(msg, prefix='config_loader', *args, **kwargs)
		else:
			raise
