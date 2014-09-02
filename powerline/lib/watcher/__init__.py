# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import sys

from powerline.lib.watcher.stat import StatFileWatcher
from powerline.lib.watcher.inotify import INotifyFileWatcher
from powerline.lib.watcher.tree import TreeWatcher
from powerline.lib.watcher.uv import UvFileWatcher, UvNotFound
from powerline.lib.inotify import INotifyError


def create_file_watcher(pl, watcher_type='auto', expire_time=10):
	'''Create an object that can watch for changes to specified files

	Use ``.__call__()`` method of the returned object to start watching the file 
	or check whether file has changed since last call.

	Use ``.unwatch()`` method of the returned object to stop watching the file.

	Uses inotify if available, then pyuv, otherwise tracks mtimes. expire_time 
	is the number of minutes after the last query for a given path for the 
	inotify watch for that path to be automatically removed. This conserves 
	kernel resources.

	:param PowerlineLogger pl:
		Logger.
	:param str watcher_type
		One of ``inotify`` (linux only), ``uv``, ``stat``, ``auto``. Determines 
		what watcher will be used. ``auto`` will use ``inotify`` if available, 
		then ``libuv`` and then fall back to ``stat``.
	:param int expire_time:
		Number of minutes since last ``.__call__()`` before inotify watcher will 
		stop watching given file.
	'''
	if watcher_type == 'stat':
		pl.debug('Using requested stat-based watcher', prefix='watcher')
		return StatFileWatcher()
	if watcher_type == 'inotify':
		# Explicitly selected inotify watcher: do not catch INotifyError then.
		pl.debug('Using requested inotify watcher', prefix='watcher')
		return INotifyFileWatcher(expire_time=expire_time)
	elif watcher_type == 'uv':
		pl.debug('Using requested uv watcher', prefix='watcher')
		return UvFileWatcher()

	if sys.platform.startswith('linux'):
		try:
			pl.debug('Trying to use inotify watcher', prefix='watcher')
			return INotifyFileWatcher(expire_time=expire_time)
		except INotifyError:
			pl.info('Failed to create inotify watcher', prefix='watcher')

	try:
		pl.debug('Using libuv-based watcher')
		return UvFileWatcher()
	except UvNotFound:
		pl.debug('Failed to import pyuv')

	pl.debug('Using stat-based watcher')
	return StatFileWatcher()


def create_tree_watcher(pl, watcher_type='auto', expire_time=10):
	'''Create an object that can watch for changes in specified directories

	:param PowerlineLogger pl:
		Logger.
	:param str watcher_type:
		Watcher type. Currently the only supported types are ``inotify`` (linux 
		only), ``uv``, ``dummy`` and ``auto``.
	:param int expire_time:
		Number of minutes since last ``.__call__()`` before inotify watcher will 
		stop watching given file.
	'''
	return TreeWatcher(pl, watcher_type, expire_time)
