# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import os
import errno

from threading import Lock
from collections import defaultdict

from powerline.lib.watcher import create_tree_watcher
from powerline.lib.unicode import out_u
from powerline.lib.path import join


def generate_directories(path):
	if os.path.isdir(path):
		yield path
	while True:
		if os.path.ismount(path):
			break
		old_path = path
		path = os.path.dirname(path)
		if path == old_path or not path:
			break
		yield path


_file_watcher = None


def file_watcher(create_watcher):
	global _file_watcher
	if _file_watcher is None:
		_file_watcher = create_watcher()
	return _file_watcher


_branch_watcher = None


def branch_watcher(create_watcher):
	global _branch_watcher
	if _branch_watcher is None:
		_branch_watcher = create_watcher()
	return _branch_watcher


branch_name_cache = {}
branch_lock = Lock()
file_status_lock = Lock()


def get_branch_name(directory, config_file, get_func, create_watcher):
	global branch_name_cache
	with branch_lock:
		# Check if the repo directory was moved/deleted
		fw = branch_watcher(create_watcher)
		is_watched = fw.is_watching(directory)
		try:
			changed = fw(directory)
		except OSError as e:
			if getattr(e, 'errno', None) != errno.ENOENT:
				raise
			changed = True
		if changed:
			branch_name_cache.pop(config_file, None)
			# Remove the watches for this repo
			if is_watched:
				fw.unwatch(directory)
				fw.unwatch(config_file)
		else:
			# Check if the config file has changed
			try:
				changed = fw(config_file)
			except OSError as e:
				if getattr(e, 'errno', None) != errno.ENOENT:
					raise
				# Config file does not exist (happens for mercurial)
				if config_file not in branch_name_cache:
					branch_name_cache[config_file] = out_u(get_func(directory, config_file))
		if changed:
			# Config file has changed or was not tracked
			branch_name_cache[config_file] = out_u(get_func(directory, config_file))
		return branch_name_cache[config_file]


class FileStatusCache(dict):
	def __init__(self):
		self.dirstate_map = defaultdict(set)
		self.ignore_map = defaultdict(set)
		self.keypath_ignore_map = {}

	def update_maps(self, keypath, directory, dirstate_file, ignore_file_name, extra_ignore_files):
		parent = keypath
		ignore_files = set()
		while parent != directory:
			nparent = os.path.dirname(keypath)
			if nparent == parent:
				break
			parent = nparent
			ignore_files.add(join(parent, ignore_file_name))
		for f in extra_ignore_files:
			ignore_files.add(f)
		self.keypath_ignore_map[keypath] = ignore_files
		for ignf in ignore_files:
			self.ignore_map[ignf].add(keypath)
		self.dirstate_map[dirstate_file].add(keypath)

	def invalidate(self, dirstate_file=None, ignore_file=None):
		for keypath in self.dirstate_map[dirstate_file]:
			self.pop(keypath, None)
		for keypath in self.ignore_map[ignore_file]:
			self.pop(keypath, None)

	def ignore_files(self, keypath):
		for ignf in self.keypath_ignore_map[keypath]:
			yield ignf


file_status_cache = FileStatusCache()


def get_file_status(directory, dirstate_file, file_path, ignore_file_name, get_func, create_watcher, extra_ignore_files=()):
	global file_status_cache
	keypath = file_path if os.path.isabs(file_path) else join(directory, file_path)
	file_status_cache.update_maps(keypath, directory, dirstate_file, ignore_file_name, extra_ignore_files)

	with file_status_lock:
		# Optimize case of keypath not being cached
		if keypath not in file_status_cache:
			file_status_cache[keypath] = ans = get_func(directory, file_path)
			return ans

		# Check if any relevant files have changed
		file_changed = file_watcher(create_watcher)
		changed = False
		# Check if dirstate has changed
		try:
			changed = file_changed(dirstate_file)
		except OSError as e:
			if getattr(e, 'errno', None) != errno.ENOENT:
				raise
			# The .git index file does not exist for a new git repo
			return get_func(directory, file_path)

		if changed:
			# Remove all cached values for files that depend on this
			# dirstate_file
			file_status_cache.invalidate(dirstate_file=dirstate_file)
		else:
			# Check if the file itself has changed
			try:
				changed ^= file_changed(keypath)
			except OSError as e:
				if getattr(e, 'errno', None) != errno.ENOENT:
					raise
				# Do not call get_func again for a non-existant file
				if keypath not in file_status_cache:
					file_status_cache[keypath] = get_func(directory, file_path)
				return file_status_cache[keypath]

			if changed:
				file_status_cache.pop(keypath, None)
			else:
				# Check if one of the ignore files has changed
				for ignf in file_status_cache.ignore_files(keypath):
					try:
						changed ^= file_changed(ignf)
					except OSError as e:
						if getattr(e, 'errno', None) != errno.ENOENT:
							raise
					if changed:
						# Invalidate cache for all files that might be affected
						# by this ignore file
						file_status_cache.invalidate(ignore_file=ignf)
						break

		try:
			return file_status_cache[keypath]
		except KeyError:
			file_status_cache[keypath] = ans = get_func(directory, file_path)
			return ans


class TreeStatusCache(dict):
	def __init__(self, pl):
		self.tw = create_tree_watcher(pl)
		self.pl = pl

	def cache_and_get(self, key, status):
		ans = self.get(key, self)
		if ans is self:
			ans = self[key] = status()
		return ans

	def __call__(self, repo):
		key = repo.directory
		try:
			if self.tw(key, ignore_event=getattr(repo, 'ignore_event', None)):
				self.pop(key, None)
		except OSError as e:
			self.pl.warn('Failed to check {0} for changes, with error: {1}', key, str(e))
		return self.cache_and_get(key, repo.status)


_tree_status_cache = None


def tree_status(repo, pl):
	global _tree_status_cache
	if _tree_status_cache is None:
		_tree_status_cache = TreeStatusCache(pl)
	return _tree_status_cache(repo)


vcs_props = (
	('git', '.git', os.path.exists),
	('mercurial', '.hg', os.path.isdir),
	('bzr', '.bzr', os.path.isdir),
)


vcs_props_bytes = [
	(vcs, vcs_dir.encode('ascii'), check)
	for vcs, vcs_dir, check in vcs_props
]


def guess(path, create_watcher):
	for directory in generate_directories(path):
		for vcs, vcs_dir, check in (vcs_props_bytes if isinstance(path, bytes) else vcs_props):
			repo_dir = os.path.join(directory, vcs_dir)
			if check(repo_dir):
				if os.path.isdir(repo_dir) and not os.access(repo_dir, os.X_OK):
					continue
				try:
					if vcs not in globals():
						globals()[vcs] = getattr(__import__(str('powerline.lib.vcs'), fromlist=[str(vcs)]), str(vcs))
					return globals()[vcs].Repository(directory, create_watcher)
				except:
					pass
	return None


def get_fallback_create_watcher():
	from powerline.lib.watcher import create_file_watcher
	from powerline import get_fallback_logger
	from functools import partial
	return partial(create_file_watcher, get_fallback_logger(), 'auto')


def debug():
	'''Test run guess(), repo.branch() and repo.status()

	To use::
		python -c 'from powerline.lib.vcs import debug; debug()' some_file_to_watch.
	'''
	import sys
	dest = sys.argv[-1]
	repo = guess(os.path.abspath(dest), get_fallback_create_watcher)
	if repo is None:
		print ('%s is not a recognized vcs repo' % dest)
		raise SystemExit(1)
	print ('Watching %s' % dest)
	print ('Press Ctrl-C to exit.')
	try:
		while True:
			if os.path.isdir(dest):
				print ('Branch name: %s Status: %s' % (repo.branch(), repo.status()))
			else:
				print ('File status: %s' % repo.status(dest))
			raw_input('Press Enter to check again: ')
	except KeyboardInterrupt:
		pass
	except EOFError:
		pass
