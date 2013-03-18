# vim:fileencoding=utf-8:noet
from __future__ import absolute_import
import os


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
