# vim:fileencoding=utf-8:noet
from __future__ import absolute_import

import os, errno
from threading import Lock


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
file_status_cache = {}
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

def get_file_status(directory, dirstate_file, file_path, ignore_file_name, get_func):
	global file_status_cache
	keypath = file_path if os.path.isabs(file_path) else os.path.join(directory, file_path)
	key = (dirstate_file, keypath)
	with file_status_lock:
		file_changed = file_watcher()
		try:
			changed = file_changed(dirstate_file) or file_changed(keypath)
		except OSError as e:
			if getattr(e, 'errno', None) != errno.ENOENT:
				raise
			if key not in file_status_cache:
				file_status_cache[key] = get_func(directory, file_path)
		else:
			parent = os.path.dirname(keypath)
			while not changed:
				try:
					changed ^= file_changed(os.path.join(parent, ignore_file_name))
				except OSError as e:
					if getattr(e, 'errno', None) != errno.ENOENT:
						raise
				if parent == directory:
					break
				nparent = os.path.dirname(parent)
				if not nparent or nparent == parent:
					break
			if changed:
				file_status_cache[key] = get_func(directory, file_path)
		return file_status_cache[key]


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
