# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, absolute_import, print_function)

__copyright__ = '2013, Kovid Goyal <kovid at kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import sys
import os
import errno
from time import sleep
from powerline.lib.monotonic import monotonic

from powerline.lib.inotify import INotify, INotifyError


class NoSuchDir(ValueError):
	pass

class BaseDirChanged(ValueError):
	pass

class DirTooLarge(ValueError):

	def __init__(self, bdir):
		ValueError.__init__(self, 'The directory {0} is too large to monitor. Try increasing the value in /proc/sys/fs/inotify/max_user_watches'.format(bdir))

def realpath(path):
	return os.path.abspath(os.path.realpath(path))

class INotifyTreeWatcher(INotify):

	is_dummy = False

	def __init__(self, basedir):
		super(INotifyTreeWatcher, self).__init__()
		self.basedir = realpath(basedir)
		self.watch_tree()
		self.modified = True

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
		import ctypes
		bpath = path if isinstance(path, bytes) else path.encode(self.fenc)
		wd = self._add_watch(self._inotify_fd, ctypes.c_char_p(bpath),
				# Ignore symlinks and watch only directories
				self.DONT_FOLLOW | self.ONLYDIR |

				self.MODIFY | self.CREATE | self.DELETE |
				self.MOVE_SELF | self.MOVED_FROM | self.MOVED_TO |
				self.ATTRIB | self.MOVE_SELF | self.DELETE_SELF)
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
			self.modified = True
			if mask & self.CREATE:
				# A new sub-directory might have been created, monitor it.
				try:
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


class DummyTreeWatcher(object):

	is_dummy = True

	def __init__(self, basedir):
		self.basedir = realpath(basedir)

	def __call__(self):
		return False

class TreeWatcher(object):

	def __init__(self, expire_time=10):
		self.watches = {}
		self.last_query_times = {}
		self.expire_time = expire_time * 60

	def watch(self, path, logger=None):
		path = realpath(path)
		try:
			w = INotifyTreeWatcher(path)
		except (INotifyError, DirTooLarge) as e:
			if logger is not None:
				logger.warn('Failed to watch path: {0} with error: {1}'.format(path, e))
			w = DummyTreeWatcher(path)
		self.watches[path] = w
		return w

	def is_actually_watched(self, path):
		w = self.watches.get(path, None)
		return not getattr(w, 'is_dummy', True)

	def expire_old_queries(self):
		pop = []
		now = monotonic()
		for path, lt in self.last_query_times.items():
			if now - lt > self.expire_time:
				pop.append(path)
		for path in pop:
			del self.last_query_times[path]

	def __call__(self, path, logger=None):
		path = realpath(path)
		self.expire_old_queries()
		self.last_query_times[path] = monotonic()
		w = self.watches.get(path, None)
		if w is None:
			try:
				self.watch(path)
			except NoSuchDir:
				pass
			return True
		try:
			return w()
		except BaseDirChanged:
			self.watches.pop(path, None)
			return True
		except DirTooLarge as e:
			if logger is not None:
				logger.warn(str(e))
			self.watches[path] = DummyTreeWatcher(path)
			return False

if __name__ == '__main__':
	w = INotifyTreeWatcher(sys.argv[-1])
	w()
	print ('Monitoring', sys.argv[-1], 'press Ctrl-C to stop')
	try:
		while True:
			if w():
				print (sys.argv[-1], 'changed')
			sleep(1)
	except KeyboardInterrupt:
		raise SystemExit(0)
