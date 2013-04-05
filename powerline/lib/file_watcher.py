# vim:fileencoding=UTF-8:noet
from __future__ import unicode_literals, absolute_import

__copyright__ = '2013, Kovid Goyal <kovid at kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os
import sys
import errno
from time import sleep
from threading import RLock

from powerline.lib.monotonic import monotonic

class INotifyError(Exception):
	pass


class INotifyWatch(object):

	is_stat_based = False

	# See <sys/inotify.h> for the flags defined below

	# Supported events suitable for MASK parameter of INOTIFY_ADD_WATCH.
	ACCESS = 0x00000001         # File was accessed.
	MODIFY = 0x00000002         # File was modified.
	ATTRIB = 0x00000004         # Metadata changed.
	CLOSE_WRITE = 0x00000008    # Writtable file was closed.
	CLOSE_NOWRITE = 0x00000010  # Unwrittable file closed.
	OPEN = 0x00000020           # File was opened.
	MOVED_FROM = 0x00000040     # File was moved from X.
	MOVED_TO = 0x00000080       # File was moved to Y.
	CREATE = 0x00000100         # Subfile was created.
	DELETE = 0x00000200         # Subfile was deleted.
	DELETE_SELF = 0x00000400    # Self was deleted.
	MOVE_SELF = 0x00000800      # Self was moved.

	# Events sent by the kernel.
	UNMOUNT = 0x00002000     # Backing fs was unmounted.
	Q_OVERFLOW = 0x00004000  # Event queued overflowed.
	IGNORED = 0x00008000     # File was ignored.

	# Helper events.
	CLOSE = (CLOSE_WRITE | CLOSE_NOWRITE)  # Close.
	MOVE = (MOVED_FROM | MOVED_TO)         # Moves.

	# Special flags.
	ONLYDIR = 0x01000000      # Only watch the path if it is a directory.
	DONT_FOLLOW = 0x02000000  # Do not follow a sym link.
	EXCL_UNLINK = 0x04000000  # Exclude events on unlinked objects.
	MASK_ADD = 0x20000000     # Add to the mask of an already existing watch.
	ISDIR = 0x40000000        # Event occurred against dir.
	ONESHOT = 0x80000000      # Only send event once.

	# All events which a program can wait on.
	ALL_EVENTS = (ACCESS | MODIFY | ATTRIB | CLOSE_WRITE | CLOSE_NOWRITE |
					OPEN | MOVED_FROM | MOVED_TO | CREATE | DELETE |
					DELETE_SELF | MOVE_SELF)

	# See <bits/inotify.h>
	CLOEXEC = 0x80000
	NONBLOCK = 0x800

	def __init__(self, inotify_fd, add_watch, rm_watch, read, expire_time=10):
		import ctypes
		import struct
		self._add_watch, self._rm_watch = add_watch, rm_watch
		self._read = read
		# We keep a reference to os to prevent it from being deleted
		# during interpreter shutdown, which would lead to errors in the
		# __del__ method
		self.os = os
		self.watches = {}
		self.modified = {}
		self.last_query = {}
		self._buf = ctypes.create_string_buffer(5000)
		self.fenc = sys.getfilesystemencoding() or 'utf-8'
		self.hdr = struct.Struct(b'iIII')
		if self.fenc == 'ascii':
			self.fenc = 'utf-8'
		self.lock = RLock()
		self.expire_time = expire_time * 60
		self._inotify_fd = inotify_fd

	def handle_error(self):
		import ctypes
		eno = ctypes.get_errno()
		raise OSError(eno, self.os.strerror(eno))

	def __del__(self):
		# This method can be called during interpreter shutdown, which means we
		# must do the absolute minimum here. Note that there could be running
		# daemon threads that are trying to call other methods on this object.
		try:
			self.os.close(self._inotify_fd)
		except (AttributeError, TypeError):
			pass

	def read(self):
		import ctypes
		buf = []
		while True:
			num = self._read(self._inotify_fd, self._buf, len(self._buf))
			if num == 0:
				break
			if num < 0:
				en = ctypes.get_errno()
				if en == errno.EAGAIN:
					break  # No more data
				if en == errno.EINTR:
					continue  # Interrupted, try again
				raise OSError(en, self.os.strerror(en))
			buf.append(self._buf.raw[:num])
		raw = b''.join(buf)
		pos = 0
		lraw = len(raw)
		while lraw - pos >= self.hdr.size:
			wd, mask, cookie, name_len = self.hdr.unpack_from(raw, pos)
			# We dont care about names as we only watch files
			pos += self.hdr.size + name_len
			self.process_event(wd, mask, cookie)

	def expire_watches(self):
		now = monotonic()
		for path, last_query in tuple(self.last_query.items()):
			if last_query - now > self.expire_time:
				self.unwatch(path)

	def process_event(self, wd, mask, cookie):
		for path, num in tuple(self.watches.items()):
			if num == wd:
				if mask & self.IGNORED:
					self.watches.pop(path, None)
					self.modified.pop(path, None)
					self.last_query.pop(path, None)
				else:
					self.modified[path] = True

	def unwatch(self, path):
		''' Remove the watch for path. Raises an OSError if removing the watch
		fails for some reason. '''
		path = self.os.path.abspath(path)
		with self.lock:
			self.modified.pop(path, None)
			self.last_query.pop(path, None)
			wd = self.watches.pop(path, None)
			if wd is not None:
				if self._rm_watch(self._inotify_fd, wd) != 0:
					self.handle_error()

	def watch(self, path):
		''' Register a watch for the file named path. Raises an OSError if path
		does not exist. '''
		import ctypes
		path = self.os.path.abspath(path)
		with self.lock:
			if path not in self.watches:
				bpath = path if isinstance(path, bytes) else path.encode(self.fenc)
				wd = self._add_watch(self._inotify_fd, ctypes.c_char_p(bpath),
						self.MODIFY | self.ATTRIB | self.MOVE_SELF | self.DELETE_SELF)
				if wd == -1:
					self.handle_error()
				self.watches[path] = wd
				self.modified[path] = False

	def __call__(self, path):
		''' Return True if path has been modified since the last call. Can
		raise OSError if the path does not exist. '''
		path = self.os.path.abspath(path)
		with self.lock:
			self.last_query[path] = monotonic()
			self.expire_watches()
			if path not in self.watches:
				# Try to re-add the watch, it will fail if the file does not
				# exist/you dont have permission
				self.watch(path)
				return True
			self.read()
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
			if hasattr(self, '_inotify_fd'):
				self.os.close(self._inotify_fd)
				del self.os
				del self._add_watch
				del self._rm_watch
				del self._inotify_fd


def get_inotify(expire_time=10):
	''' Initialize the inotify based file watcher '''
	import ctypes
	if not hasattr(ctypes, 'c_ssize_t'):
		raise INotifyError('You need python >= 2.7 to use inotify')
	from ctypes.util import find_library
	name = find_library('c')
	if not name:
		raise INotifyError('Cannot find C library')
	libc = ctypes.CDLL(name, use_errno=True)
	for function in ("inotify_add_watch", "inotify_init1", "inotify_rm_watch"):
		if not hasattr(libc, function):
			raise INotifyError('libc is too old')
	# inotify_init1()
	prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, use_errno=True)
	init1 = prototype(('inotify_init1', libc), ((1, "flags", 0),))

	# inotify_add_watch()
	prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32, use_errno=True)
	add_watch = prototype(('inotify_add_watch', libc), (
		(1, "fd"), (1, "pathname"), (1, "mask")), use_errno=True)

	# inotify_rm_watch()
	prototype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, use_errno=True)
	rm_watch = prototype(('inotify_rm_watch', libc), (
		(1, "fd"), (1, "wd")), use_errno=True)

	# read()
	prototype = ctypes.CFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, use_errno=True)
	read = prototype(('read', libc), (
		(1, "fd"), (1, "buf"), (1, "count")), use_errno=True)

	inotify_fd = init1(INotifyWatch.CLOEXEC | INotifyWatch.NONBLOCK)
	if inotify_fd == -1:
		raise INotifyError(os.strerror(ctypes.get_errno()))
	return INotifyWatch(inotify_fd, add_watch, rm_watch, read, expire_time=expire_time)


class StatWatch(object):
	is_stat_based = True

	def __init__(self):
		self.watches = {}
		self.lock = RLock()

	def watch(self, path):
		path = os.path.abspath(path)
		with self.lock:
			self.watches[path] = os.path.getmtime(path)

	def unwatch(self, path):
		path = os.path.abspath(path)
		with self.lock:
			self.watches.pop(path, None)

	def __call__(self, path):
		path = os.path.abspath(path)
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
		return get_inotify(expire_time=expire_time)
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
