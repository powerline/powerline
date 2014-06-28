# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import

import errno
import os

from threading import RLock

from powerline.lib.inotify import INotify
from powerline.lib.monotonic import monotonic
from powerline.lib.path import realpath


class INotifyFileWatcher(INotify):
	def __init__(self, expire_time=10):
		super(INotifyFileWatcher, self).__init__()
		self.watches = {}
		self.modified = {}
		self.last_query = {}
		self.lock = RLock()
		self.expire_time = expire_time * 60

	def expire_watches(self):
		now = monotonic()
		for path, last_query in tuple(self.last_query.items()):
			if last_query - now > self.expire_time:
				self.unwatch(path)

	def process_event(self, wd, mask, cookie, name):
		if wd == -1 and (mask & self.Q_OVERFLOW):
			# We missed some INOTIFY events, so we dont
			# know the state of any tracked files.
			for path in tuple(self.modified):
				if os.path.exists(path):
					self.modified[path] = True
				else:
					self.watches.pop(path, None)
					self.modified.pop(path, None)
					self.last_query.pop(path, None)
			return

		for path, num in tuple(self.watches.items()):
			if num == wd:
				if mask & self.IGNORED:
					self.watches.pop(path, None)
					self.modified.pop(path, None)
					self.last_query.pop(path, None)
				else:
					if mask & self.ATTRIB:
						# The watched file could have had its inode changed, in
						# which case we will not get any more events for this
						# file, so re-register the watch. For example by some
						# other file being renamed as this file.
						try:
							self.unwatch(path)
						except OSError:
							pass
						try:
							self.watch(path)
						except OSError as e:
							if getattr(e, 'errno', None) != errno.ENOENT:
								raise
						else:
							self.modified[path] = True
					else:
						self.modified[path] = True

	def unwatch(self, path):
		''' Remove the watch for path. Raises an OSError if removing the watch
		fails for some reason. '''
		path = realpath(path)
		with self.lock:
			self.modified.pop(path, None)
			self.last_query.pop(path, None)
			wd = self.watches.pop(path, None)
			if wd is not None:
				if self._rm_watch(self._inotify_fd, wd) != 0:
					self.handle_error()

	def watch(self, path):
		''' Register a watch for the file/directory named path. Raises an OSError if path
		does not exist. '''
		import ctypes
		path = realpath(path)
		with self.lock:
			if path not in self.watches:
				bpath = path if isinstance(path, bytes) else path.encode(self.fenc)
				flags = self.MOVE_SELF | self.DELETE_SELF
				buf = ctypes.c_char_p(bpath)
				# Try watching path as a directory
				wd = self._add_watch(self._inotify_fd, buf, flags | self.ONLYDIR)
				if wd == -1:
					eno = ctypes.get_errno()
					if eno != errno.ENOTDIR:
						self.handle_error()
					# Try watching path as a file
					flags |= (self.MODIFY | self.ATTRIB)
					wd = self._add_watch(self._inotify_fd, buf, flags)
					if wd == -1:
						self.handle_error()
				self.watches[path] = wd
				self.modified[path] = False

	def is_watched(self, path):
		with self.lock:
			return realpath(path) in self.watches

	def __call__(self, path):
		''' Return True if path has been modified since the last call. Can
		raise OSError if the path does not exist. '''
		path = realpath(path)
		with self.lock:
			self.last_query[path] = monotonic()
			self.expire_watches()
			if path not in self.watches:
				# Try to re-add the watch, it will fail if the file does not
				# exist/you dont have permission
				self.watch(path)
				return True
			self.read(get_name=False)
			if path not in self.modified:
				# An ignored event was received which means the path has been
				# automatically unwatched
				return True
			ans = self.modified[path]
			if ans:
				self.modified[path] = False
			return ans

	def close(self):
		with self.lock:
			for path in tuple(self.watches):
				try:
					self.unwatch(path)
				except OSError:
					pass
			super(INotifyFileWatcher, self).close()
