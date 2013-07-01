# vim:fileencoding=utf-8:noet
from __future__ import unicode_literals, absolute_import

__copyright__ = '2013, Kovid Goyal <kovid at kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import sys
import os
import errno


class INotifyError(Exception):
	pass


_inotify = None


def load_inotify():
	''' Initialize the inotify library '''
	global _inotify
	if _inotify is None:
		if hasattr(sys, 'getwindowsversion'):
			# On windows abort before loading the C library. Windows has
			# multiple, incompatible C runtimes, and we have no way of knowing
			# if the one chosen by ctypes is compatible with the currently
			# loaded one.
			raise INotifyError('INotify not available on windows')
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
		_inotify = (init1, add_watch, rm_watch, read)
	return _inotify


class INotify(object):

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

	def __init__(self, cloexec=True, nonblock=True):
		import ctypes
		import struct
		self._init1, self._add_watch, self._rm_watch, self._read = load_inotify()
		flags = 0
		if cloexec:
			flags |= self.CLOEXEC
		if nonblock:
			flags |= self.NONBLOCK
		self._inotify_fd = self._init1(flags)
		if self._inotify_fd == -1:
			raise INotifyError(os.strerror(ctypes.get_errno()))

		self._buf = ctypes.create_string_buffer(5000)
		self.fenc = sys.getfilesystemencoding() or 'utf-8'
		self.hdr = struct.Struct(b'iIII')
		if self.fenc == 'ascii':
			self.fenc = 'utf-8'
		# We keep a reference to os to prevent it from being deleted
		# during interpreter shutdown, which would lead to errors in the
		# __del__ method
		self.os = os

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

	def close(self):
		if hasattr(self, '_inotify_fd'):
			self.os.close(self._inotify_fd)
			del self.os
			del self._add_watch
			del self._rm_watch
			del self._inotify_fd

	def read(self, get_name=True):
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
			pos += self.hdr.size
			name = None
			if get_name:
				name = raw[pos:pos + name_len].rstrip(b'\0').decode(self.fenc)
			pos += name_len
			self.process_event(wd, mask, cookie, name)

	def process_event(self, *args):
		raise NotImplementedError()
