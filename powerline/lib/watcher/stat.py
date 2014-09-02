# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os

from threading import RLock

from powerline.lib.path import realpath


class StatFileWatcher(object):
	def __init__(self):
		self.watches = {}
		self.lock = RLock()

	def watch(self, path):
		path = realpath(path)
		with self.lock:
			self.watches[path] = os.path.getmtime(path)

	def unwatch(self, path):
		path = realpath(path)
		with self.lock:
			self.watches.pop(path, None)

	def is_watching(self, path):
		with self.lock:
			return realpath(path) in self.watches

	def __call__(self, path):
		path = realpath(path)
		with self.lock:
			if path not in self.watches:
				self.watches[path] = os.path.getmtime(path)
				return True
			mtime = os.path.getmtime(path)
			if mtime != self.watches[path]:
				self.watches[path] = mtime
				return True
			return False

	def close(self):
		with self.lock:
			self.watches.clear()
