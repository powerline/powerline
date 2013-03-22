# vim:fileencoding=utf-8:noet
from __future__ import absolute_import

import os
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
branch_lock = Lock()

def get_branch_name(directory, config_file, get_func):
	global branch_name_cache
	with branch_lock:
		try:
			changed = file_watcher()(config_file)
		except OSError:
			# Config file does not exist (happens for mercurial)
			if config_file not in branch_name_cache:
				branch_name_cache[config_file] = get_func(directory, config_file)
		else:
			if changed:
				# Config file has changed or was not tracked
				branch_name_cache[config_file] = get_func(directory, config_file)
		return branch_name_cache[config_file]

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
