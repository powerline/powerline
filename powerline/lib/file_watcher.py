# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import

__copyright__ = '2013, Kovid Goyal <kovid at kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os
import sys
import errno
from time import sleep
from threading import RLock

from powerline.lib.monotonic import monotonic
from powerline.lib.inotify import INotify, INotifyError

def realpath(path):
	return os.path.abspath(os.path.realpath(path))

class INotifyWatch(INotify):

	is_stat_based = False

	def __init__(self, expire_time=10):
		super(INotifyWatch, self).__init__()
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
			super(INotifyWatch, self).close()


class StatWatch(object):
	is_stat_based = True

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

	def is_watched(self, path):
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


def create_file_watcher(use_stat=False, expire_time=10):
	'''
	Create an object that can watch for changes to specified files. To use:

	watcher = create_file_watcher()
	watcher(path1) # Will return True if path1 has changed since the last time this was called. Always returns True the first time.
	watcher.unwatch(path1)

	Uses inotify if available, otherwise tracks mtimes. expire_time is the
	number of minutes after the last query for a given path for the inotify
	watch for that path to be automatically removed. This conserves kernel
	resources.
	'''
	if use_stat:
		return StatWatch()
	try:
		return INotifyWatch(expire_time=expire_time)
	except INotifyError:
		pass
	return StatWatch()

if __name__ == '__main__':
	watcher = create_file_watcher()
	print ('Using watcher: %s' % watcher.__class__.__name__)
	print ('Watching %s, press Ctrl-C to quit' % sys.argv[-1])
	watcher.watch(sys.argv[-1])
	try:
		while True:
			if watcher(sys.argv[-1]):
				print ('%s has changed' % sys.argv[-1])
			sleep(1)
	except KeyboardInterrupt:
		pass
	watcher.close()
