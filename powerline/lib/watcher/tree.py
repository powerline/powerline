# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.lib.monotonic import monotonic
from powerline.lib.inotify import INotifyError
from powerline.lib.path import realpath
from powerline.lib.watcher.inotify import INotifyTreeWatcher, DirTooLarge, NoSuchDir, BaseDirChanged
from powerline.lib.watcher.uv import UvTreeWatcher, UvNotFound


class DummyTreeWatcher(object):
	is_dummy = True

	def __init__(self, basedir):
		self.basedir = realpath(basedir)

	def __call__(self):
		return False


class TreeWatcher(object):
	def __init__(self, pl, watcher_type, expire_time):
		self.watches = {}
		self.last_query_times = {}
		self.expire_time = expire_time * 60
		self.pl = pl
		self.watcher_type = watcher_type

	def get_watcher(self, path, ignore_event):
		if self.watcher_type == 'inotify':
			return INotifyTreeWatcher(path, ignore_event=ignore_event)
		if self.watcher_type == 'uv':
			return UvTreeWatcher(path, ignore_event=ignore_event)
		if self.watcher_type == 'dummy':
			return DummyTreeWatcher(path)
		# FIXME
		if self.watcher_type == 'stat':
			return DummyTreeWatcher(path)
		if self.watcher_type == 'auto':
			if sys.platform.startswith('linux'):
				try:
					return INotifyTreeWatcher(path, ignore_event=ignore_event)
				except (INotifyError, DirTooLarge) as e:
					if not isinstance(e, INotifyError):
						self.pl.warn('Failed to watch path: {0} with error: {1}'.format(path, e))
			try:
				return UvTreeWatcher(path, ignore_event=ignore_event)
			except UvNotFound:
				pass
			return DummyTreeWatcher(path)
		else:
			raise ValueError('Unknown watcher type: {0}'.format(self.watcher_type))

	def watch(self, path, ignore_event=None):
		path = realpath(path)
		w = self.get_watcher(path, ignore_event)
		self.watches[path] = w
		return w

	def expire_old_queries(self):
		pop = []
		now = monotonic()
		for path, lt in self.last_query_times.items():
			if now - lt > self.expire_time:
				pop.append(path)
		for path in pop:
			del self.last_query_times[path]

	def __call__(self, path, ignore_event=None):
		path = realpath(path)
		self.expire_old_queries()
		self.last_query_times[path] = monotonic()
		w = self.watches.get(path, None)
		if w is None:
			try:
				self.watch(path, ignore_event=ignore_event)
			except NoSuchDir:
				pass
			return True
		try:
			return w()
		except BaseDirChanged:
			self.watches.pop(path, None)
			return True
		except DirTooLarge as e:
			self.pl.warn(str(e))
			self.watches[path] = DummyTreeWatcher(path)
			return False
