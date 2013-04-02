# vim:fileencoding=utf-8:noet
from __future__ import absolute_import

import os, errno
from threading import Lock
from collections import defaultdict

vcs_props = (
	('git', '.git', os.path.exists),
	('mercurial', '.hg', os.path.isdir),
	('bzr', '.bzr', os.path.isdir),
)


def generate_directories(path):
	yield path
	while True:
		old_path = path
		path = os.path.dirname(path)
		if path == old_path or not path:
			break
		yield path

_file_watcher = None

def file_watcher():
	global _file_watcher
	if _file_watcher is None:
		from powerline.lib.file_watcher import create_file_watcher
		_file_watcher = create_file_watcher()
	return _file_watcher

branch_name_cache = {}
branch_lock = Lock()
file_status_lock = Lock()

def get_branch_name(directory, config_file, get_func):
	global branch_name_cache
	with branch_lock:
		try:
			changed = file_watcher()(config_file)
		except OSError as e:
			if getattr(e, 'errno', None) != errno.ENOENT:
				raise
			# Config file does not exist (happens for mercurial)
			if config_file not in branch_name_cache:
				branch_name_cache[config_file] = get_func(directory, config_file)
		else:
			if changed:
				# Config file has changed or was not tracked
				branch_name_cache[config_file] = get_func(directory, config_file)
		return branch_name_cache[config_file]

class FileStatusCache(dict):

	def __init__(self):
		self.dirstate_map = defaultdict(set)
		self.ignore_map = defaultdict(set)
		self.keypath_ignore_map = {}

	def update_maps(self, keypath, directory, dirstate_file, ignore_file_name):
		parent = keypath
		ignore_files = set()
		while parent != directory:
			nparent = os.path.dirname(keypath)
			if nparent == parent:
				break
			parent = nparent
			ignore_files.add(os.path.join(parent, ignore_file_name))
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

def get_file_status(directory, dirstate_file, file_path, ignore_file_name, get_func):
	global file_status_cache
	keypath = file_path if os.path.isabs(file_path) else os.path.join(directory, file_path)
	file_status_cache.update_maps(keypath, directory, dirstate_file, ignore_file_name)

	with file_status_lock:
		# Optimize case of keypath not being cached
		if keypath not in file_status_cache:
			file_status_cache[keypath] = ans = get_func(directory, file_path)
			return ans

		# Check if any relevant files have changed
		file_changed = file_watcher()
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

def guess(path):
	for directory in generate_directories(path):
		for vcs, vcs_dir, check in vcs_props:
			if check(os.path.join(directory, vcs_dir)):
				try:
					if vcs not in globals():
						globals()[vcs] = getattr(__import__('powerline.lib.vcs', fromlist=[vcs]), vcs)
					return globals()[vcs].Repository(directory)
				except:
					pass
	return None
