# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import errno
import os
import ctypes

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

	def is_watching(self, path):
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


class NoSuchDir(ValueError):
	pass


class BaseDirChanged(ValueError):
	pass


class DirTooLarge(ValueError):
	def __init__(self, bdir):
		ValueError.__init__(self, 'The directory {0} is too large to monitor. Try increasing the value in /proc/sys/fs/inotify/max_user_watches'.format(bdir))


class INotifyTreeWatcher(INotify):
	is_dummy = False

	def __init__(self, basedir, ignore_event=None):
		super(INotifyTreeWatcher, self).__init__()
		self.basedir = realpath(basedir)
		self.watch_tree()
		self.modified = True
		self.ignore_event = (lambda path, name: False) if ignore_event is None else ignore_event

	def watch_tree(self):
		self.watched_dirs = {}
		self.watched_rmap = {}
		try:
			self.add_watches(self.basedir)
		except OSError as e:
			if e.errno == errno.ENOSPC:
				raise DirTooLarge(self.basedir)

	def add_watches(self, base, top_level=True):
		''' Add watches for this directory and all its descendant directories,
		recursively. '''
		base = realpath(base)
		# There may exist a link which leads to an endless
		# add_watches loop or to maximum recursion depth exceeded
		if not top_level and base in self.watched_dirs:
			return
		try:
			is_dir = self.add_watch(base)
		except OSError as e:
			if e.errno == errno.ENOENT:
				# The entry could have been deleted between listdir() and
				# add_watch().
				if top_level:
					raise NoSuchDir('The dir {0} does not exist'.format(base))
				return
			if e.errno == errno.EACCES:
				# We silently ignore entries for which we dont have permission,
				# unless they are the top level dir
				if top_level:
					raise NoSuchDir('You do not have permission to monitor {0}'.format(base))
				return
			raise
		else:
			if is_dir:
				try:
					files = os.listdir(base)
				except OSError as e:
					if e.errno in (errno.ENOTDIR, errno.ENOENT):
						# The dir was deleted/replaced between the add_watch()
						# and listdir()
						if top_level:
							raise NoSuchDir('The dir {0} does not exist'.format(base))
						return
					raise
				for x in files:
					self.add_watches(os.path.join(base, x), top_level=False)
			elif top_level:
				# The top level dir is a file, not good.
				raise NoSuchDir('The dir {0} does not exist'.format(base))

	def add_watch(self, path):
		bpath = path if isinstance(path, bytes) else path.encode(self.fenc)
		wd = self._add_watch(
			self._inotify_fd,
			ctypes.c_char_p(bpath),

			# Ignore symlinks and watch only directories
			self.DONT_FOLLOW | self.ONLYDIR |

			self.MODIFY | self.CREATE | self.DELETE |
			self.MOVE_SELF | self.MOVED_FROM | self.MOVED_TO |
			self.ATTRIB | self.DELETE_SELF
		)
		if wd == -1:
			eno = ctypes.get_errno()
			if eno == errno.ENOTDIR:
				return False
			raise OSError(eno, 'Failed to add watch for: {0}: {1}'.format(path, self.os.strerror(eno)))
		self.watched_dirs[path] = wd
		self.watched_rmap[wd] = path
		return True

	def process_event(self, wd, mask, cookie, name):
		if wd == -1 and (mask & self.Q_OVERFLOW):
			# We missed some INOTIFY events, so we dont
			# know the state of any tracked dirs.
			self.watch_tree()
			self.modified = True
			return
		path = self.watched_rmap.get(wd, None)
		if path is not None:
			if not self.ignore_event(path, name):
				self.modified = True
			if mask & self.CREATE:
				# A new sub-directory might have been created, monitor it.
				try:
					if not isinstance(path, bytes):
						name = name.decode(self.fenc)
					self.add_watch(os.path.join(path, name))
				except OSError as e:
					if e.errno == errno.ENOENT:
						# Deleted before add_watch()
						pass
					elif e.errno == errno.ENOSPC:
						raise DirTooLarge(self.basedir)
					else:
						raise
			if (mask & self.DELETE_SELF or mask & self.MOVE_SELF) and path == self.basedir:
				raise BaseDirChanged('The directory %s was moved/deleted' % path)

	def __call__(self):
		self.read()
		ret = self.modified
		self.modified = False
		return ret
