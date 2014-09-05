# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from collections import defaultdict
from threading import RLock
from functools import partial
from threading import Thread

from powerline.lib.path import realpath


class UvNotFound(NotImplementedError):
	pass


pyuv = None


def import_pyuv():
	global pyuv
	if not pyuv:
		try:
			pyuv = __import__('pyuv')
		except ImportError:
			raise UvNotFound


class UvThread(Thread):
	daemon = True

	def __init__(self, loop):
		self.uv_loop = loop
		super(UvThread, self).__init__()

	def run(self):
		while True:
			self.uv_loop.run()

	def join(self):
		self.uv_loop.stop()
		return super(UvThread, self).join()


_uv_thread = None


def start_uv_thread():
	global _uv_thread
	if _uv_thread is None:
		loop = pyuv.Loop()
		_uv_thread = UvThread(loop)
		_uv_thread.start()
	return _uv_thread.uv_loop


class UvWatcher(object):
	def __init__(self):
		import_pyuv()
		self.watches = {}
		self.lock = RLock()
		self.loop = start_uv_thread()

	def watch(self, path):
		path = realpath(path)
		with self.lock:
			if path not in self.watches:
				try:
					self.watches[path] = pyuv.fs.FSEvent(
						self.loop,
						path,
						partial(self._record_event, path),
						pyuv.fs.UV_CHANGE | pyuv.fs.UV_RENAME
					)
				except pyuv.error.FSEventError as e:
					code = e.args[0]
					if code == pyuv.errno.UV_ENOENT:
						raise OSError('No such file or directory: ' + path)
					else:
						raise

	def unwatch(self, path):
		path = realpath(path)
		with self.lock:
			try:
				watch = self.watches.pop(path)
			except KeyError:
				return
		watch.close(partial(self._stopped_watching, path))

	def is_watching(self, path):
		with self.lock:
			return realpath(path) in self.watches

	def __del__(self):
		try:
			lock = self.lock
		except AttributeError:
			pass
		else:
			with lock:
				while self.watches:
					path, watch = self.watches.popitem()
					watch.close(partial(self._stopped_watching, path))


class UvFileWatcher(UvWatcher):
	def __init__(self):
		super(UvFileWatcher, self).__init__()
		self.events = defaultdict(list)

	def _record_event(self, path, fsevent_handle, filename, events, error):
		with self.lock:
			self.events[path].append(events)
			if events | pyuv.fs.UV_RENAME:
				if not os.path.exists(path):
					self.watches.pop(path).close()

	def _stopped_watching(self, path, *args):
		self.events.pop(path, None)

	def __call__(self, path):
		path = realpath(path)
		with self.lock:
			events = self.events.pop(path, None)
		if events:
			return True
		if path not in self.watches:
			self.watch(path)
			return True
		return False


class UvTreeWatcher(UvWatcher):
	is_dummy = False

	def __init__(self, basedir, ignore_event=None):
		super(UvTreeWatcher, self).__init__()
		self.ignore_event = ignore_event or (lambda path, name: False)
		self.basedir = realpath(basedir)
		self.modified = True
		self.watch_directory(self.basedir)

	def watch_directory(self, path):
		os.path.walk(realpath(path), self.watch_one_directory, None)

	def watch_one_directory(self, arg, dirname, fnames):
		try:
			self.watch(dirname)
		except OSError:
			pass

	def _stopped_watching(self, path, *args):
		pass

	def _record_event(self, path, fsevent_handle, filename, events, error):
		if not self.ignore_event(path, filename):
			self.modified = True
			if events == pyuv.fs.UV_CHANGE | pyuv.fs.UV_RENAME:
				# Stat changes to watched directory are UV_CHANGE|UV_RENAME. It 
				# is weird.
				pass
			elif events | pyuv.fs.UV_RENAME:
				if not os.path.isdir(path):
					self.unwatch(path)
				else:
					full_name = os.path.join(path, filename)
					if os.path.isdir(full_name):
						# For some reason mkdir and rmdir both fall into this 
						# category
						self.watch_directory(full_name)

	def __call__(self):
		return self.__dict__.pop('modified', False)
